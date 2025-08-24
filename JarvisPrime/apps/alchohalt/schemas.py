import datetime as dt
from typing import Optional, Dict, List, Any
from pydantic import BaseModel
from enum import Enum


class StatusEnum(str, Enum):
    halted = "halted"
    slipped = "slipped"

class UserCreate(BaseModel):
    email: str
    tz: str
    reminder_hour: int = 21

class UserRead(BaseModel):
    id: int

class CheckinCreate(BaseModel):
    user_id: int
    status: StatusEnum
    date: Optional[dt.date] = None
    note: Optional[str] = None

class StreaksRead(BaseModel):
    current_streak_days: int
    longest_streak_days: int
    last_30: Dict[str, int]

class ExportData(BaseModel):
    user: Dict[str, Any]
    checkins: List[Dict[str, Any]]

class ImportData(BaseModel):
    user: Dict[str, Any]
    checkins: List[Dict[str, Any]]
