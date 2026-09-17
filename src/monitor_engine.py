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
            appointments = self.check_ecari()
        except Exception as e:
            print("eCARI-Abfrage fehlgeschlagen:", e)
            self.job.last_error = "eCARI-Abfrage fehlgeschlagen"
            self.job.status = "waiting"
            return []

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

    def check_ecari(self):
        c = self.job.config

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            try:
                page.goto(
                    ECARI_URL,
                    wait_until="commit",
                    timeout=60000,
                )

                page.wait_for_timeout(5000)

                print("eCARI geöffnet:", page.url)

                inputs = page.locator("input")
                input_count = inputs.count()

                print("Anzahl Eingabefelder:", input_count)

                # Ohne Zugangsdaten nur die Erreichbarkeit testen.
                if not c.halter_nummer or not c.geburtsdatum:
                    print("Keine eCARI-Zugangsdaten vorhanden.")
                    return []

                if input_count < 2:
                    raise RuntimeError(
                        "eCARI-Loginfelder wurden nicht gefunden."
                    )

                # Die beiden Loginfelder:
                # 1. Halter-Nummer
                # 2. Geburtsdatum
                inputs.nth(0).fill(c.halter_nummer)
                inputs.nth(1).fill(c.geburtsdatum)

                print("eCARI-Zugangsdaten wurden eingegeben.")

                # Login-Schaltfläche suchen.
                login_button = page.get_by_role(
                    "button",
                    name="Anmelden",
                    exact=True,
                )

                if login_button.count() == 0:
                    login_button = page.get_by_role(
                        "button",
                        name="Weiter",
                        exact=True,
                    )

                if login_button.count() == 0:
                    raise RuntimeError(
                        "Login-Schaltfläche wurde nicht gefunden."
                    )

                login_button.first.click()

                page.wait_for_timeout(5000)

                print("Nach Login:", page.url)
                print("Seitentitel nach Login:", page.title())

                # Noch keine Terminbuchung.
                # Wir prüfen zunächst nur, ob der Login erfolgreich war.
                body_text = page.locator("body").inner_text(
                    timeout=10000
                )

                print("eCARI nach Login geladen.")
                print(body_text[:5000])

                return []

            finally:
                browser.close()

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
