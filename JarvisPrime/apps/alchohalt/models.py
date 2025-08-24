from datetime import datetime, date
from typing import Optional
from sqlmodel import SQLModel, Field, UniqueConstraint
from uuid import uuid4

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str
    tz: str
    reminder_hour: int = 21
    public_id: str = Field(default_factory=lambda: uuid4().hex)
    phone: Optional[str] = None
    caregiver_email: Optional[str] = None
    consent_caregiver: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Checkin(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    date: date
    status: str
    note: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    __table_args__ = (UniqueConstraint("user_id", "date"),)


class CaregiverLink(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    caregiver_email: str
    role: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    __table_args__ = (UniqueConstraint("user_id", "caregiver_email"),)


class AlertPref(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    channel: str
    threshold: str
    quiet_hours_start: Optional[int] = None
    quiet_hours_end: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    __table_args__ = (UniqueConstraint("user_id", "channel", "threshold"),)
