from datetime import datetime, timedelta, date
from typing import Iterable, List
from zoneinfo import ZoneInfo
from sqlmodel import Session, select
from pathlib import Path
import csv
import json
import smtplib
import requests
from .models import User, Checkin, AlertPref, CaregiverLink
from .settings import get_settings
from .auth import mask_email
from .crypto import encrypt_note, decrypt_note, encryption_enabled, is_encrypted

settings = get_settings()
LOG_FILE = Path(settings.log_dir) / "alchohalt.jsonl"
LOG_FILE.parent.mkdir(exist_ok=True, parents=True)


def due_reminders(session: Session, now_utc: datetime) -> Iterable[User]:
    for user in session.exec(select(User)):
        local = now_utc.astimezone(ZoneInfo(user.tz))
        if local.hour == user.reminder_hour:
            yield user

def send_email(email: str, subject: str, body: str, dry_run: bool = False) -> None:
    settings = get_settings()
    if dry_run or not settings.smtp_host:
        print(f"Reminder to {mask_email(email)}: {subject}")
        return
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port or 0) as smtp:
            if settings.smtp_user and settings.smtp_pass:
                smtp.login(settings.smtp_user, settings.smtp_pass)
            msg = f"Subject: {subject}\n\n{body}"
            smtp.sendmail(settings.smtp_user or "", [email], msg)
    except Exception:
        print("log-only: email send failed")


def send_sms(phone: str, body: str, dry_run: bool = False) -> None:
    settings = get_settings()
    masked = phone[:-2] + "**"
    if dry_run or not (settings.twilio_sid and settings.twilio_token and settings.twilio_from):
        print(f"sms to {masked}: {body}")
        return
    try:
        url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.twilio_sid}/Messages.json"
        data = {"From": settings.twilio_from, "To": phone, "Body": body}
        requests.post(url, data=data, auth=(settings.twilio_sid, settings.twilio_token), timeout=10)
    except Exception:
        print("log-only: sms send failed")

def calculate_streaks(session: Session, user: User, today: datetime.date):
    checkins = session.exec(select(Checkin).where(Checkin.user_id == user.id)).all()
    by_date = {c.date: c for c in checkins}
    current = 0
    d = today
    while True:
        c = by_date.get(d)
        if c and c.status == "halted":
            current += 1
            d -= timedelta(days=1)
        else:
            break
    longest = 0
    run = 0
    prev = None
    for day in sorted(by_date):
        c = by_date[day]
        if c.status == "halted" and (prev is None or day == prev + timedelta(days=1)):
            run += 1
        elif c.status == "halted":
            run = 1
        else:
            run = 0
        longest = max(longest, run)
        prev = day
    start = today - timedelta(days=29)
    counts = {"halted": 0, "slipped": 0}
    for day, c in by_date.items():
        if start <= day <= today and c.status in counts:
            counts[c.status] += 1
    return {
        "current_streak_days": current,
        "longest_streak_days": longest,
        "last_30": counts,
    }


def to_csv_rows(checkins: List[Checkin], include_notes: bool = False):
    for c in checkins:
        row = {"date": c.date.isoformat(), "status": c.status}
        if include_notes:
            note = decrypt_note(c.note)
            if note is None and is_encrypted(c.note):
                row["note"] = "[encrypted]"
            elif note:
                row["note"] = note
            else:
                row["note"] = ""
        yield row


def from_csv_rows(rows: Iterable[dict]):
    parsed = []
    for row in rows:
        date_str = row.get("date")
        status = row.get("status")
        note = row.get("note") or None
        if not date_str or status not in {"halted", "slipped"}:
            raise ValueError("invalid row")
        parsed.append({
            "date": datetime.fromisoformat(date_str).date(),
            "status": status,
            "note": note,
        })
    return parsed


def log_event(kind: str, user_id: int, details: dict) -> None:
    entry = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "kind": kind,
        "user_id": user_id,
        "details": details,
    }
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def log_checkin(user_id: int, chk_date: datetime.date, status: str, source: str) -> None:
    log_event(
        "checkin",
        user_id,
        {"date": chk_date.isoformat(), "status": status, "source": source},
    )


def redact_old_notes(session: Session, cutoff: date) -> int:
    counts: dict[int, int] = {}
    notes = session.exec(
        select(Checkin).where(Checkin.note.is_not(None), Checkin.date < cutoff)
    ).all()
    for c in notes:
        counts[c.user_id] = counts.get(c.user_id, 0) + 1
        c.note = None
    session.commit()
    for uid, cnt in counts.items():
        log_event("retention", uid, {"removed": cnt})
    return sum(counts.values())


def send_digest_if_due(
    session: Session, user: User, now_local: datetime, dry_run: bool = False
) -> bool:
    if not user.caregiver_email:
        return False
    if not (now_local.hour == 0 and now_local.minute == 0):
        return False
    yesterday = (now_local - timedelta(days=1)).date()
    chk = session.exec(
        select(Checkin).where(Checkin.user_id == user.id, Checkin.date == yesterday)
    ).first()
    status = chk.status if chk else "no check-in"
    streaks = calculate_streaks(session, user, yesterday)
    link = f"/alchohalt/care/{user.public_id}"
    body = f"{status} today; streak {streaks['current_streak_days']}; {link}"
    send_email(user.caregiver_email, "Alchohalt digest", body, dry_run=dry_run)
    log_event("digest", user.id, {"status": status})
    return True


def gather_metrics(session: Session) -> dict:
    users = session.exec(select(User)).all()
    checkins = session.exec(select(Checkin)).all()
    today = datetime.utcnow().date()
    start = today - timedelta(days=29)
    halted_30 = sum(1 for c in checkins if start <= c.date <= today and c.status == "halted")
    slipped_30 = sum(1 for c in checkins if start <= c.date <= today and c.status == "slipped")
    due_count = sum(
        1
        for u in users
        if datetime.utcnow().astimezone(ZoneInfo(u.tz)).hour == u.reminder_hour
    )
    caregiver_enabled = sum(1 for u in users if u.caregiver_email)
    return {
        "users": len(users),
        "checkins_total": len(checkins),
        "halted_30": halted_30,
        "slipped_30": slipped_30,
        "daily_due_count": due_count,
        "encrypted_notes": encryption_enabled(),
        "retention_days": settings.retention_days,
        "caregiver_enabled_count": caregiver_enabled,
    }


def evaluate_alerts_for(session: Session, user: User, now_local: datetime) -> list[dict]:
    prefs = session.exec(select(AlertPref).where(AlertPref.user_id == user.id)).all()
    if not prefs:
        return []
    today = now_local.date()
    start7 = today - timedelta(days=6)
    start30 = today - timedelta(days=29)
    slips7 = session.exec(
        select(Checkin)
        .where(Checkin.user_id == user.id, Checkin.date >= start7)
        .where(Checkin.status == "slipped")
    ).all()
    slips30 = session.exec(
        select(Checkin)
        .where(Checkin.user_id == user.id, Checkin.date >= start30)
        .where(Checkin.status == "slipped")
    ).all()
    today_chk = session.exec(
        select(Checkin).where(Checkin.user_id == user.id, Checkin.date == today)
    ).first()
    events = []
    for pref in prefs:
        hour = now_local.hour
        if (
            pref.quiet_hours_start is not None
            and pref.quiet_hours_end is not None
            and pref.quiet_hours_start <= pref.quiet_hours_end
            and pref.quiet_hours_start <= hour < pref.quiet_hours_end
        ):
            continue
        reason = None
        if pref.threshold == "slip" and today_chk and today_chk.status == "slipped":
            reason = "slip"
        elif pref.threshold == "two_in_7" and len(slips7) >= 2:
            reason = "two_in_7"
        elif pref.threshold == "three_in_30" and len(slips30) >= 3:
            reason = "three_in_30"
        if reason:
            events.append({"channel": pref.channel, "reason": reason})
    return events


def notify_caregivers(session: Session, user: User, events: list[dict], dry_run: bool = False) -> dict:
    if not events:
        return {"alerts_sent": 0, "reasons": []}
    links = session.exec(
        select(CaregiverLink).where(CaregiverLink.user_id == user.id, CaregiverLink.role == "supporter")
    ).all()
    reasons = [e["reason"] for e in events]
    count = 0
    for link in links:
        for e in events:
            body = f"Alert: {e['reason']} for user {user.public_id}. /alchohalt/care/{user.public_id}"
            if e["channel"] == "email":
                send_email(link.caregiver_email, "Alchohalt alert", body, dry_run=dry_run)
                count += 1
            elif e["channel"] == "sms" and user.phone:
                send_sms(user.phone, body, dry_run=dry_run)
                count += 1
    log_event(
        "alert",
        user.id,
        {"rules_triggered": reasons, "channels": [e["channel"] for e in events], "count": count},
    )
    return {"alerts_sent": count, "reasons": reasons}


def run_notifier(session: Session, now: datetime, dry_run: bool = False) -> None:
    reminders = 0
    for user in due_reminders(session, now):
        send_email(user.email, "Alchohalt reminder", "Time to check in.", dry_run=dry_run)
        if user.phone:
            send_sms(user.phone, "Time to check in.", dry_run=dry_run)
        reminders += 1
    digests = 0
    alerts = 0
    for user in session.exec(select(User)):
        local = now.astimezone(ZoneInfo(user.tz))
        if send_digest_if_due(session, user, local, dry_run=dry_run):
            digests += 1
        events = evaluate_alerts_for(session, user, local)
        res = notify_caregivers(session, user, events, dry_run=dry_run)
        alerts += res["alerts_sent"]
    if settings.retention_days > 0:
        cutoff = now.date() - timedelta(days=settings.retention_days)
        removed = redact_old_notes(session, cutoff)
        if removed:
            print(f"retention removed {removed} notes")
    log_event(
        "notifier_summary",
        0,
        {"reminders": reminders, "digests": digests, "alerts": alerts},
    )
