from datetime import datetime
from playwright.sync_api import sync_playwright

from app.models import Appointment


ECARI_URL = (
    "https://portal.stva.zh.ch/"
    "ecari-dispoweb/ui/app/init/"
    "#/conduite/prive/login"
)


class MonitorEngine:
    def __init__(self, job, notifier=None):
        self.job = job
        self.notifier = notifier

    def run_check(self):
        self.job.checks += 1
        self.job.last_check = datetime.utcnow()
        self.job.status = "checking"

        # Test: eCARI mit Playwright öffnen
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            page.goto(
                ECARI_URL,
                wait_until="domcontentloaded",
                timeout=30000,
            )

            print("eCARI erreichbar:", page.url)

            browser.close()

        # Bis die echte Terminsuche eingebaut ist,
        # verwenden wir weiterhin die Test-Termine.
        appointments = self.get_test_appointments()

        new = []

        for a in appointments:
            if a.id in self.job.reported_ids:
                continue

            if not self.matches_filters(a):
                continue

            self.job.reported_ids.add(a.id)
            new.append(a)

        self.job.appointments_found += len(new)
        self.job.status = "waiting"

        return new

    def matches_filters(self, a):
        c = self.job.config

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
            Appointment("2026-10-10", "08:00", "Zürich"),
            Appointment("2026-10-10", "10:30", "Zürich"),
            Appointment("2026-10-15", "14:00", "Winterthur"),
            Appointment("2026-11-02", "09:15", "Bülach"),
        ]
