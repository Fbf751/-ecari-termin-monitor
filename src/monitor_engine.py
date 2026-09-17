from dataclasses import dataclass
from datetime import datetime
from playwright.sync_api import sync_playwright

@dataclass(frozen=True)
class Appointment:
    date: str
    time: str
    location: str

    @property
    def id(self):
        return f"{self.date}|{self.time}|{self.location}"

class MonitorEngine:
    """Safe test engine. Real eCARI access is intentionally not enabled yet."""

    def __init__(self, job, notifier=None):
        self.job=job
        self.notifier=notifier

    def run_check(self):
        self.job.checks += 1
        self.job.last_check=datetime.utcnow()
        self.job.status="checking"

        appointments=self.get_test_appointments()
        new=[]
        for a in appointments:
            if a.id in self.job.reported_ids:
                continue
            if not self.matches_filters(a):
                continue
            self.job.reported_ids.add(a.id)
            new.append(a)

        self.job.appointments_found += len(new)
        self.job.status="waiting"
        return new

    def matches_filters(self,a):
        c=self.job.config
        if c.location and c.location.lower() not in a.location.lower():
            return False
        if c.date_from and a.date < c.date_from:
            return False
        if c.date_to and a.date > c.date_to:
            return False
        return True

    @staticmethod
    def get_test_appointments():
        return [
            Appointment("2026-10-10","08:00","Zürich"),
            Appointment("2026-10-10","10:30","Zürich"),
            Appointment("2026-10-15","14:00","Winterthur"),
            Appointment("2026-11-02","09:15","Bülach"),
        ]
