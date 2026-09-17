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

                    print("=== ECARI TESTMONITOR ===")
                    print("URL:", page.url)
                    print("TITLE:", page.title())
                    print("=== INPUT-FELDER ===")

                    inputs = page.locator("input")
                    print("ANZAHL INPUTS:", inputs.count())

                    for i in range(inputs.count()):
                        element = inputs.nth(i)

                        print(
                            f"INPUT {i}: "
                            f"name={element.get_attribute('name')} | "
                            f"type={element.get_attribute('type')} | "
                            f"placeholder={element.get_attribute('placeholder')}"
                        )

                    print("=== BUTTONS ===")

                    buttons = page.locator("button")
                    print("ANZAHL BUTTONS:", buttons.count())

                    for i in range(buttons.count()):
                        element = buttons.nth(i)

                        print(
                            f"BUTTON {i}: "
                            f"text={element.inner_text()} | "
                            f"type={element.get_attribute('type')}"
                        )

                    print("=== ENDE ECARI TEST ===")

                except Exception as e:
                    print("eCARI konnte nicht vollständig geladen werden:", e)

                finally:
                    browser.close()

        except Exception as e:
            print("Playwright-Test fehlgeschlagen:", e)

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
