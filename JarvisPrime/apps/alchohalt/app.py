from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, Request
from pydantic import BaseModel, ValidationError
from fastapi.responses import Response, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import SQLModel, Session, select
import datetime as dt
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import csv
import io
import subprocess
from .models import User, Checkin, CaregiverLink, AlertPref
from .schemas import (
    UserCreate,
    UserRead,
    CheckinCreate,
    StreaksRead,
    ImportData,
    StatusEnum,
)
from .settings import get_engine, get_settings
from .service import (
    calculate_streaks,
    to_csv_rows,
    from_csv_rows,
    gather_metrics,
    log_checkin,
    send_email,
)
from .crypto import encrypt_note, decrypt_note, encryption_enabled
from collections import defaultdict
from .auth import (
    issue_magic_link,
    verify_token,
    sign_session,
    verify_session,
    audit_event,
    mask_email,
    require_session,
    require_owner,
    issue_caregiver_invite,
    verify_caregiver_invite,
)
from .ui import router as ui_router

app = FastAPI()
engine = get_engine()
templates = Jinja2Templates(directory="apps/alchohalt/templates")
app.mount("/alchohalt/static", StaticFiles(directory="apps/alchohalt/static"), name="alchohalt-static")
app.include_router(ui_router, prefix="/alchohalt/ui")
app.state.rate_counts = defaultdict(int)


def _utcnow() -> datetime:
    return datetime.utcnow()


class BulkItem(BaseModel):
    status: str
    date: dt.date | None = None
    note: str | None = None


class BulkPayload(BaseModel):
    user_id: int
    items: list[BulkItem]


class LinkRequest(UserCreate):
    pass


class CaregiverIn(BaseModel):
    user_id: int
    caregiver_email: str
    role: str


class CaregiverDelete(BaseModel):
    user_id: int
    caregiver_email: str


class AlertPrefIn(BaseModel):
    user_id: int
    channel: str
    threshold: str
    quiet_hours_start: int | None = None
    quiet_hours_end: int | None = None


class ConsentIn(BaseModel):
    user_id: int
    consent: bool



def get_session():
    with Session(engine) as session:
        yield session

@app.on_event("startup")
def on_startup() -> None:
    SQLModel.metadata.create_all(engine)
    app.state.rate_counts.clear()

@app.get("/alchohalt/health")
def health(session: Session = Depends(get_session)):
    commit = ""
    try:
        commit = (
            subprocess.check_output(["git", "rev-parse", "--short", "HEAD"])
            .decode()
            .strip()
        )
    except Exception:
        commit = "unknown"
    db_ok = True
    try:
        session.exec(select(1))
    except Exception:
        db_ok = False
    settings = get_settings()
    return {
        "ok": True,
        "commit": commit,
        "db": db_ok,
        "encryption_enabled": encryption_enabled(),
        "retention_days": settings.retention_days,
    }


@app.post("/alchohalt/request_link")
def request_link(data: LinkRequest, request: Request, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == data.email)).first()
    if not user:
        user = User(email=data.email, tz=data.tz, reminder_hour=data.reminder_hour)
        session.add(user)
        session.commit()
        session.refresh(user)
    token = issue_magic_link(user.email)
    link = f"/alchohalt/magic?token={token}"
    send_email(user.email, "Alchohalt link", link)
    print(f"magic link: {link}")
    audit_event(request, "magic_link_requested", email=user.email)
    return {"ok": True}


@app.get("/alchohalt/magic")
def magic(token: str, request: Request, session: Session = Depends(get_session)):
    email = verify_token(token)
    if not email:
        raise HTTPException(400, "invalid or expired token")
    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        raise HTTPException(404, "user not found")
    cookie = sign_session(user.id)
    resp = RedirectResponse(url="/alchohalt/ui", status_code=303)
    resp.set_cookie("alc_session", cookie, httponly=True, max_age=30 * 24 * 3600)
    audit_event(request, "session_established", user_id=user.id, email=user.email)
    return resp


@app.post("/alchohalt/logout")
def logout(request: Request):
    uid = None
    token = request.cookies.get("alc_session")
    if token:
        uid = verify_session(token)
    resp = RedirectResponse(url="/alchohalt/ui", status_code=303)
    resp.delete_cookie("alc_session")
    audit_event(request, "logout", user_id=uid)
    return resp

@app.post("/alchohalt/users", response_model=UserRead)
def create_user(user: UserCreate, session: Session = Depends(get_session)):
    db_user = User(email=user.email, tz=user.tz, reminder_hour=user.reminder_hour)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    app.state.rate_counts.pop((db_user.id, _utcnow().date()), None)
    return UserRead(id=db_user.id)

@app.post("/alchohalt/checkins")
def create_checkin(data: CheckinCreate, request: Request, session: Session = Depends(get_session)):
    require_owner(request, data.user_id)
    user = session.get(User, data.user_id)
    if not user:
        raise HTTPException(404, "user not found")
    now = _utcnow()
    key = (user.id, now.date())
    count = app.state.rate_counts[key]
    if count >= 5:
        next_day = datetime.combine(now.date() + timedelta(days=1), datetime.min.time())
        retry = int((next_day - now).total_seconds())
        raise HTTPException(429, "rate limit exceeded", headers={"Retry-After": str(retry)})
    app.state.rate_counts[key] = count + 1
    chk_date = data.date or datetime.now(ZoneInfo(user.tz)).date()
    existing = session.exec(
        select(Checkin).where(Checkin.user_id == user.id, Checkin.date == chk_date)
    ).first()
    note_val = encrypt_note(data.note)
    if existing:
        existing.status = data.status
        existing.note = note_val
    else:
        session.add(Checkin(user_id=user.id, date=chk_date, status=data.status, note=note_val))
    session.commit()
    log_checkin(user.id, chk_date, data.status, "api")
    audit_event(request, "checkin_write", user_id=user.id)
    return {"ok": True}


@app.post("/alchohalt/checkins/bulk")
def bulk_checkins(payload: BulkPayload, request: Request, session: Session = Depends(get_session)):
    require_owner(request, payload.user_id)
    user = session.get(User, payload.user_id)
    if not user:
        raise HTTPException(404, "user not found")
    results = []
    for item in payload.items:
        try:
            chk = CheckinCreate(user_id=payload.user_id, status=item.status, date=item.date, note=item.note)
        except ValidationError:
            raise HTTPException(400, "invalid item")
        chk_date = chk.date or datetime.now(ZoneInfo(user.tz)).date()
        existing = session.exec(
            select(Checkin).where(Checkin.user_id == user.id, Checkin.date == chk_date)
        ).first()
        note_val = encrypt_note(chk.note)
        if existing:
            existing.status = chk.status
            existing.note = note_val
        else:
            session.add(Checkin(user_id=user.id, date=chk_date, status=chk.status, note=note_val))
        log_checkin(user.id, chk_date, chk.status, "api")
        results.append({"date": chk_date.isoformat(), "status": chk.status})
    session.commit()
    audit_event(request, "checkin_write", user_id=user.id)
    return {"processed": len(results), "items": results}

@app.get("/alchohalt/streaks/{user_id}", response_model=StreaksRead)
def streaks(user_id: int, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(404, "user not found")
    today = datetime.now(ZoneInfo(user.tz)).date()
    return calculate_streaks(session, user, today)

@app.get("/alchohalt/export/{user_id}")
def export_data(user_id: int, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(404, "user not found")
    checkins = session.exec(select(Checkin).where(Checkin.user_id == user.id)).all()
    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "tz": user.tz,
            "reminder_hour": user.reminder_hour,
            "public_id": user.public_id,
        },
        "checkins": [
            {
                "date": c.date.isoformat(),
                "status": c.status,
                "note": decrypt_note(c.note),
            }
            for c in checkins
        ],
    }

@app.post("/alchohalt/import")
def import_data(payload: ImportData, session: Session = Depends(get_session)):
    user_data = payload.user
    existing = session.exec(select(User).where(User.email == user_data["email"])).first()
    if existing:
        existing.tz = user_data.get("tz", existing.tz)
        existing.reminder_hour = user_data.get("reminder_hour", existing.reminder_hour)
        user_id = existing.id
    else:
        new_user = User(**user_data)
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
        user_id = new_user.id
    for item in payload.checkins:
        chk_date = datetime.fromisoformat(item["date"]).date()
        existing_chk = session.exec(
            select(Checkin).where(Checkin.user_id == user_id, Checkin.date == chk_date)
        ).first()
        note_val = encrypt_note(item.get("note"))
        if existing_chk:
            existing_chk.status = item["status"]
            existing_chk.note = note_val
        else:
            session.add(
                Checkin(user_id=user_id, date=chk_date, status=item["status"], note=note_val)
            )
    session.commit()
    return {"id": user_id}


@app.get("/alchohalt/export_csv/{user_id}")
def export_csv(user_id: int, request: Request, include_notes: int = 0, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(404, "user not found")
    checkins = session.exec(select(Checkin).where(Checkin.user_id == user.id)).all()
    include = bool(include_notes)
    fields = ["date", "status"] + (["note"] if include else [])
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fields)
    writer.writeheader()
    for row in to_csv_rows(checkins, include_notes=include):
        writer.writerow(row)
    audit_event(request, "export_csv", user_id=user.id)
    return Response(buf.getvalue(), media_type="text/csv")


@app.post("/alchohalt/import_csv")
async def import_csv(
    request: Request,
    file: UploadFile = File(...),
    email: str = Form(...),
    tz: str = Form(...),
    reminder_hour: int = Form(21),
    session: Session = Depends(get_session),
):
    content = (await file.read()).decode("utf-8")
    rows = from_csv_rows(csv.DictReader(io.StringIO(content)))
    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        user = User(email=email, tz=tz, reminder_hour=reminder_hour)
        session.add(user)
        session.commit()
        session.refresh(user)
    else:
        user.tz = tz
        user.reminder_hour = reminder_hour
    for row in rows:
        existing = session.exec(
            select(Checkin).where(Checkin.user_id == user.id, Checkin.date == row["date"])
        ).first()
        if existing:
            existing.status = row["status"]
            existing.note = row["note"]
        else:
            session.add(
                Checkin(
                    user_id=user.id,
                    date=row["date"],
                    status=row["status"],
                    note=row["note"],
                )
            )
    session.commit()
    audit_event(request, "import_csv", user_id=user.id)
    return {"id": user.id}


@app.get("/alchohalt/metrics")
def metrics(session: Session = Depends(get_session)):
    return gather_metrics(session)


@app.post("/alchohalt/consent")
def set_consent(data: ConsentIn, request: Request, session: Session = Depends(get_session)):
    require_owner(request, data.user_id)
    user = session.get(User, data.user_id)
    if not user:
        raise HTTPException(404, "user not found")
    user.consent_caregiver = data.consent
    session.commit()
    return {"ok": True}


@app.post("/alchohalt/caregivers")
def add_caregiver(data: CaregiverIn, request: Request, session: Session = Depends(get_session)):
    require_owner(request, data.user_id)
    if data.role not in {"viewer", "supporter"}:
        raise HTTPException(400, "invalid role")
    user = session.get(User, data.user_id)
    if not user:
        raise HTTPException(404, "user not found")
    if not user.consent_caregiver:
        raise HTTPException(403, "caregiver consent required")
    link = CaregiverLink(user_id=user.id, caregiver_email=data.caregiver_email, role=data.role)
    session.add(link)
    try:
        session.commit()
    except Exception:
        session.rollback()
        raise HTTPException(400, "duplicate")
    return {"ok": True}


@app.delete("/alchohalt/caregivers")
def del_caregiver(data: CaregiverDelete, request: Request, session: Session = Depends(get_session)):
    require_owner(request, data.user_id)
    link = session.exec(
        select(CaregiverLink).where(
            CaregiverLink.user_id == data.user_id, CaregiverLink.caregiver_email == data.caregiver_email
        )
    ).first()
    if not link:
        raise HTTPException(404, "not found")
    session.delete(link)
    session.commit()
    return {"ok": True}


@app.get("/alchohalt/caregivers/{user_id}")
def list_caregivers(user_id: int, session: Session = Depends(get_session)):
    links = session.exec(select(CaregiverLink).where(CaregiverLink.user_id == user_id)).all()
    return [
        {"caregiver_email": mask_email(l.caregiver_email), "role": l.role} for l in links
    ]


@app.post("/alchohalt/alert_prefs")
def upsert_alert_pref(data: AlertPrefIn, request: Request, session: Session = Depends(get_session)):
    require_owner(request, data.user_id)
    if data.channel not in {"email", "sms"} or data.threshold not in {"slip", "two_in_7", "three_in_30"}:
        raise HTTPException(400, "invalid")
    user = session.get(User, data.user_id)
    if not user:
        raise HTTPException(404, "user not found")
    pref = session.exec(
        select(AlertPref).where(
            AlertPref.user_id == user.id,
            AlertPref.channel == data.channel,
            AlertPref.threshold == data.threshold,
        )
    ).first()
    if pref:
        pref.quiet_hours_start = data.quiet_hours_start
        pref.quiet_hours_end = data.quiet_hours_end
    else:
        session.add(
            AlertPref(
                user_id=user.id,
                channel=data.channel,
                threshold=data.threshold,
                quiet_hours_start=data.quiet_hours_start,
                quiet_hours_end=data.quiet_hours_end,
            )
        )
    session.commit()
    return {"ok": True}


@app.post("/alchohalt/invite_caregiver")
def invite_caregiver(
    request: Request,
    user_id: int = Form(...),
    caregiver_email: str = Form(...),
    role: str = Form(...),
    session: Session = Depends(get_session),
):
    require_session(request)
    require_owner(request, user_id)
    if role not in {"viewer", "supporter"}:
        raise HTTPException(400, "invalid role")
    token = issue_caregiver_invite(user_id, caregiver_email, role)
    link = f"/alchohalt/accept_caregiver?token={token}"
    send_email(caregiver_email, "Alchohalt invite", link)
    return {"ok": True}


@app.get("/alchohalt/accept_caregiver")
def accept_caregiver(token: str, session: Session = Depends(get_session)):
    payload = verify_caregiver_invite(token)
    if not payload:
        raise HTTPException(400, "invalid or expired token")
    user = session.get(User, payload["user_id"])
    if not user:
        raise HTTPException(404, "user not found")
    if not user.consent_caregiver:
        return Response("caregiver consent required", media_type="text/plain", status_code=403)
    link = CaregiverLink(
        user_id=user.id, caregiver_email=payload["caregiver_email"], role=payload["role"]
    )
    session.add(link)
    try:
        session.commit()
    except Exception:
        session.rollback()
    return RedirectResponse(url=f"/alchohalt/care/{user.public_id}", status_code=303)


@app.get("/alchohalt/alert_prefs/{user_id}")
def list_alert_prefs(user_id: int, session: Session = Depends(get_session)):
    prefs = session.exec(select(AlertPref).where(AlertPref.user_id == user_id)).all()
    return [
        {
            "channel": p.channel,
            "threshold": p.threshold,
            "quiet_hours_start": p.quiet_hours_start,
            "quiet_hours_end": p.quiet_hours_end,
        }
        for p in prefs
    ]


@app.get("/alchohalt/care/{public_id}")
def caregiver(public_id: str, request: Request, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.public_id == public_id)).first()
    if not user:
        raise HTTPException(404, "not found")
    today = datetime.now(ZoneInfo(user.tz)).date()
    streaks = calculate_streaks(session, user, today)
    recent = session.exec(
        select(Checkin)
        .where(Checkin.user_id == user.id)
        .order_by(Checkin.date.desc())
        .limit(30)
    ).all()
    clean = [{"date": c.date, "status": c.status} for c in recent]
    return templates.TemplateResponse(
        "caregiver.html",
        {
            "request": request,
            "streaks": streaks,
            "recent": clean,
        },
    )
