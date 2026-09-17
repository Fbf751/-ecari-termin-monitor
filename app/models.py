from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class MonitorRequest:
    halter_nummer: str
    geburtsdatum: str
    date_from: str
    date_to: str
    location: str
    telegram_token: str
    telegram_chat_id: str
    duration_minutes: int = 120
    interval_minutes: int = 12


@dataclass
class MonitorJob:
    job_id: str
    config: MonitorRequest
    created_at: datetime
    expires_at: datetime
    status: str = "starting"
    checks: int = 0
    appointments_found: int = 0
    last_check: Optional[datetime] = None
    last_error: Optional[str] = None
    reported_ids: set = field(default_factory=set)


@dataclass
class Appointment:
    date: str
    time: str
    location: str

    @property
    def id(self):
        return f"{self.date}|{self.time}|{self.location}"
