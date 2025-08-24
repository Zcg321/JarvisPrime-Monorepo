import os
from functools import lru_cache
from typing import Optional
from sqlmodel import create_engine
from sqlalchemy.pool import StaticPool
from functools import lru_cache

class Settings:
    def __init__(self) -> None:
        self.db_url: str = os.getenv("ALC_DB_URL", "sqlite:///./alchohalt.db")
        self.smtp_host: Optional[str] = os.getenv("ALC_SMTP_HOST")
        port = os.getenv("ALC_SMTP_PORT")
        self.smtp_port: Optional[int] = int(port) if port else None
        self.smtp_user: Optional[str] = os.getenv("ALC_SMTP_USER")
        self.smtp_pass: Optional[str] = os.getenv("ALC_SMTP_PASS")
        self.secret: str = os.getenv("ALC_SECRET", "dev-secret")
        self.twilio_sid: Optional[str] = os.getenv("ALC_TWILIO_SID")
        self.twilio_token: Optional[str] = os.getenv("ALC_TWILIO_TOKEN")
        self.twilio_from: Optional[str] = os.getenv("ALC_TWILIO_FROM")
        self.crypto_key: Optional[str] = os.getenv("ALC_CRYPTO_KEY")
        self.retention_days: int = int(os.getenv("ALC_RETENTION_DAYS", "0"))
        self.log_dir: str = os.getenv("ALC_LOG_DIR", "logs")

@lru_cache()
def get_settings() -> Settings:
    return Settings()

@lru_cache()
def get_engine():
    settings = get_settings()
    if settings.db_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
        if settings.db_url == "sqlite://":
            return create_engine(settings.db_url, connect_args=connect_args, poolclass=StaticPool)
        return create_engine(settings.db_url, connect_args=connect_args)
    return create_engine(settings.db_url)
