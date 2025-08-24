from fastapi import APIRouter, Depends, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from datetime import datetime
from zoneinfo import ZoneInfo
from .models import User, Checkin, CaregiverLink, AlertPref
from .service import calculate_streaks, log_checkin
from .settings import get_engine
from .auth import verify_session, mask_email

router = APIRouter()
engine = get_engine()
templates = Jinja2Templates(directory="apps/alchohalt/templates")


def get_session():
    with Session(engine) as session:
        yield session


@router.get("", response_class=HTMLResponse)
def dashboard(request: Request, session: Session = Depends(get_session)):
    cookie = request.cookies.get("alc_session")
    user_id = verify_session(cookie) if cookie else None
    if not user_id:
        return templates.TemplateResponse("login.html", {"request": request})
    user = session.get(User, user_id)
    if not user:
        return templates.TemplateResponse("login.html", {"request": request})
    today = datetime.now(ZoneInfo(user.tz)).date()
    streaks = calculate_streaks(session, user, today)
    recent = session.exec(
        select(Checkin).where(Checkin.user_id == user.id).order_by(Checkin.date.desc()).limit(30)
    ).all()
    caregivers = session.exec(select(CaregiverLink).where(CaregiverLink.user_id == user.id)).all()
    prefs = session.exec(select(AlertPref).where(AlertPref.user_id == user.id)).all()
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
            "masked_email": mask_email(user.email),
            "streaks": streaks,
            "recent": recent,
            "caregivers": caregivers,
            "prefs": prefs,
        },
    )


@router.get("/checkin")
def checkin_form(request: Request, session: Session = Depends(get_session)):
    cookie = request.cookies.get("alc_session")
    user_id = verify_session(cookie) if cookie else None
    if not user_id:
        return templates.TemplateResponse("login.html", {"request": request})
    user = session.get(User, user_id)
    if not user:
        return templates.TemplateResponse("login.html", {"request": request})
    return templates.TemplateResponse("checkin.html", {"request": request})


@router.post("/checkin")
def post_checkin(
    request: Request,
    status: str = Form(...),
    note: str | None = Form(None),
    session: Session = Depends(get_session),
):
    cookie = request.cookies.get("alc_session")
    user_id = verify_session(cookie) if cookie else None
    if not user_id:
        raise HTTPException(401, "no session")
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(404, "user not found")
    chk_date = datetime.now(ZoneInfo(user.tz)).date()
    existing = session.exec(
        select(Checkin).where(Checkin.user_id == user.id, Checkin.date == chk_date)
    ).first()
    if existing:
        existing.status = status
        existing.note = note
    else:
        session.add(Checkin(user_id=user.id, date=chk_date, status=status, note=note))
    session.commit()
    log_checkin(user.id, chk_date, status, "ui")
    return RedirectResponse(url="/alchohalt/ui", status_code=303)


@router.post("/consent")
def post_consent(request: Request, consent: bool = Form(False), session: Session = Depends(get_session)):
    cookie = request.cookies.get("alc_session")
    user_id = verify_session(cookie) if cookie else None
    if not user_id:
        raise HTTPException(401, "no session")
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(404, "user not found")
    user.consent_caregiver = consent
    session.commit()
    return RedirectResponse(url="/alchohalt/ui", status_code=303)


@router.post("/caregivers/add")
def ui_add_caregiver(
    request: Request,
    caregiver_email: str = Form(...),
    role: str = Form(...),
    session: Session = Depends(get_session),
):
    cookie = request.cookies.get("alc_session")
    user_id = verify_session(cookie) if cookie else None
    if not user_id:
        raise HTTPException(401, "no session")
    user = session.get(User, user_id)
    if not user or not user.consent_caregiver:
        raise HTTPException(403, "consent required")
    link = CaregiverLink(user_id=user.id, caregiver_email=caregiver_email, role=role)
    session.add(link)
    session.commit()
    return RedirectResponse(url="/alchohalt/ui", status_code=303)


@router.post("/caregivers/delete")
def ui_del_caregiver(
    request: Request,
    caregiver_email: str = Form(...),
    session: Session = Depends(get_session),
):
    cookie = request.cookies.get("alc_session")
    user_id = verify_session(cookie) if cookie else None
    if not user_id:
        raise HTTPException(401, "no session")
    link = session.exec(
        select(CaregiverLink).where(
            CaregiverLink.user_id == user_id, CaregiverLink.caregiver_email == caregiver_email
        )
    ).first()
    if link:
        session.delete(link)
        session.commit()
    return RedirectResponse(url="/alchohalt/ui", status_code=303)


@router.post("/alert_prefs")
def ui_alert_pref(
    request: Request,
    channel: str = Form(...),
    threshold: str = Form(...),
    quiet_hours_start: int | None = Form(None),
    quiet_hours_end: int | None = Form(None),
    session: Session = Depends(get_session),
):
    cookie = request.cookies.get("alc_session")
    user_id = verify_session(cookie) if cookie else None
    if not user_id:
        raise HTTPException(401, "no session")
    pref = session.exec(
        select(AlertPref).where(
            AlertPref.user_id == user_id,
            AlertPref.channel == channel,
            AlertPref.threshold == threshold,
        )
    ).first()
    if pref:
        pref.quiet_hours_start = quiet_hours_start
        pref.quiet_hours_end = quiet_hours_end
    else:
        session.add(
            AlertPref(
                user_id=user_id,
                channel=channel,
                threshold=threshold,
                quiet_hours_start=quiet_hours_start,
                quiet_hours_end=quiet_hours_end,
            )
        )
    session.commit()
    return RedirectResponse(url="/alchohalt/ui", status_code=303)
