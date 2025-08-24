import os
import time
import hmac
import base64
import hashlib
import json
from pathlib import Path
from datetime import datetime
from typing import Optional
from fastapi import Request

SECRET = os.getenv("ALC_SECRET", "dev-secret")


def _sign(data: str) -> str:
    return hmac.new(SECRET.encode(), data.encode(), hashlib.sha256).hexdigest()


def issue_magic_link(email: str, expires_in: int = 900) -> str:
    exp = int(time.time()) + expires_in
    payload = f"{email}|{exp}"
    sig = _sign(payload)
    token = base64.urlsafe_b64encode(f"{payload}|{sig}".encode()).decode()
    return token


def verify_token(token: str) -> Optional[str]:
    try:
        raw = base64.urlsafe_b64decode(token.encode()).decode()
        email, exp, sig = raw.split("|")
        if _sign(f"{email}|{exp}") != sig:
            return None
        if int(exp) < int(time.time()):
            return None
        return email
    except Exception:
        return None


def sign_session(user_id: int, days: int = 30) -> str:
    exp = int(time.time()) + days * 86400
    payload = f"{user_id}|{exp}"
    sig = _sign(payload)
    return base64.urlsafe_b64encode(f"{payload}|{sig}".encode()).decode()


def verify_session(token: str) -> Optional[int]:
    try:
        raw = base64.urlsafe_b64decode(token.encode()).decode()
        user_id, exp, sig = raw.split("|")
        if _sign(f"{user_id}|{exp}") != sig:
            return None
        if int(exp) < int(time.time()):
            return None
        return int(user_id)
    except Exception:
        return None


def mask_email(email: str) -> str:
    if "@" not in email:
        return "***"
    user, domain = email.split("@", 1)
    return f"{user[0]}***@{domain}"


AUDIT_LOG = Path("logs/audit.jsonl")
AUDIT_LOG.parent.mkdir(exist_ok=True)


def audit_event(
    request: Request,
    event: str,
    user_id: Optional[int] = None,
    email: Optional[str] = None,
) -> None:
    ip = request.client.host if request.client else ""
    ip_hash = hashlib.sha256(ip.encode()).hexdigest()[:10]
    entry = {"ts": datetime.utcnow().isoformat(), "event": event, "ip_hash": ip_hash}
    if user_id is not None:
        entry["user_id"] = user_id
    if email:
        entry["email_masked"] = mask_email(email)
    with AUDIT_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def _session_user(request: Request) -> Optional[int]:
    token = request.cookies.get("alc_session")
    return verify_session(token) if token else None


def require_session(request: Request) -> int:
    uid = _session_user(request)
    if uid is None:
        from fastapi import HTTPException

        raise HTTPException(401, "session required")
    return uid


def require_owner(request: Request, user_id: int) -> None:
    uid = _session_user(request)
    if uid is not None and uid != user_id:
        from fastapi import HTTPException

        raise HTTPException(403, "forbidden")


def issue_caregiver_invite(user_id: int, caregiver_email: str, role: str, expires_in: int = 86400) -> str:
    exp = int(time.time()) + expires_in
    payload = f"{user_id}|{caregiver_email}|{role}|{exp}"
    sig = _sign(payload)
    return base64.urlsafe_b64encode(f"{payload}|{sig}".encode()).decode()


def verify_caregiver_invite(token: str) -> Optional[dict]:
    try:
        raw = base64.urlsafe_b64decode(token.encode()).decode()
        user_id, email, role, exp, sig = raw.split("|")
        if _sign(f"{user_id}|{email}|{role}|{exp}") != sig:
            return None
        if int(exp) < int(time.time()):
            return None
        return {"user_id": int(user_id), "caregiver_email": email, "role": role}
    except Exception:
        return None
