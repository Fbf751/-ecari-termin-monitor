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

        # eCARI-Test: Fehler beim Aufruf dürfen den Testlauf
        # vorerst nicht abbrechen.
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                try:
                    page.goto(
                        ECARI_URL,
                        wait_until="commit",
                        timeout=60000,
                    )

                    print("eCARI erreichbar:", page.url)
                    print("Seitentitel:", page.title())

                    print("INPUT-FELDER:")

                    for i in range(page.locator("input").count()):
                        element = page.locator("input").nth(i)

                        print(
                            "INPUT",
                            i,
                            "name=", element.get_attribute("name"),
                            "type=", element.get_attribute("type"),
                            "placeholder=", element.get_attribute("placeholder"),
                        )

                except Exception as e:
                    print(
                        "eCARI konnte aus GitHub Actions "
                        "nicht geladen werden:",
                        e,
                    )

                finally:
                    browser.close()

        except Exception as e:
            print("Playwright-Test fehlgeschlagen:", e)

        # Test-Termine
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
