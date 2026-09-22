from datetime import datetime
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

ECARI_URL = (
    "https://portal.stva.zh.ch/"
    "ecari-dispoweb/ui/app/init/"
    "#/conduite/prive/login"
)

LOCATION_NAME = "Albisgütli"

CATEGORY_LABELS = {
    "B": ["Kategorie B", "PW", "B "],
    "A1": ["Kategorie A1", "Motorrad A1", "A1"],
}

MAX_WEEKS_TO_CHECK = 20

DEBUG_DIR = Path("debug")


class EcariNavigationError(RuntimeError):
    """Raised when a step on the eCARI site doesn't match what this script
    expects. These selectors were written without access to a real logged-in
    eCARI session (the login needs a real Halter-Nummer/Geburtsdatum), so
    they are a best-effort first pass. If this fires, download the
    'debug-screenshots' artifact from the failed workflow run to see exactly
    what the site showed, then adjust the selectors in this file.
    """


def _debug_shot(page: Page, label: str) -> None:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%H%M%S")
    try:
        page.screenshot(path=str(DEBUG_DIR / f"{ts}_{label}.png"), full_page=True)
    except Exception as e:
        print(f"Screenshot fehlgeschlagen ({label}):", e)


def login(page: Page, halter_nummer: str, geburtsdatum: str) -> None:
    page.goto(ECARI_URL, wait_until="commit", timeout=60000)
    page.wait_for_timeout(5000)
    _debug_shot(page, "01_login_page")

    inputs = page.locator("input")
    if inputs.count() < 2:
        raise EcariNavigationError("Login-Eingabefelder wurden nicht gefunden.")

    inputs.nth(0).fill(halter_nummer)
    inputs.nth(1).fill(geburtsdatum)

    login_button = page.get_by_role("button", name="Anmelden", exact=True)
    if login_button.count() == 0:
        login_button = page.get_by_role("button", name="Weiter", exact=True)
    if login_button.count() == 0:
        raise EcariNavigationError("Login-Schaltfläche wurde nicht gefunden.")

    login_button.first.click()
    page.wait_for_timeout(5000)
    _debug_shot(page, "02_after_login")


def open_booking_flow(page: Page, category: str) -> None:
    """Navigate from the post-login dashboard into the appointment booking
    flow for the given exam category ("B" or "A1"). UNVERIFIED against a
    real session - see the module docstring / EcariNavigationError.
    """
    candidates = [
        "Neue Anmeldung", "Termin buchen", "Prüfung buchen",
        "Führerprüfung", "Praktische Prüfung", "Neuer Termin",
    ]

    for text in candidates:
        locator = page.get_by_text(text, exact=False)
        if locator.count() > 0:
            locator.first.click()
            break
    else:
        _debug_shot(page, "03_booking_entry_not_found")
        raise EcariNavigationError(
            "Einstieg in die Terminbuchung wurde nicht gefunden."
        )

    page.wait_for_timeout(3000)
    _debug_shot(page, "04_booking_flow_opened")

    for label in CATEGORY_LABELS.get(category, [category]):
        locator = page.get_by_text(label, exact=False)
        if locator.count() > 0:
            locator.first.click()
            break
    else:
        _debug_shot(page, "05_category_not_found")
        raise EcariNavigationError(f"Prüfungskategorie '{category}' wurde nicht gefunden.")

    page.wait_for_timeout(2000)
    _debug_shot(page, "06_category_selected")

    location_locator = page.get_by_text(LOCATION_NAME, exact=False)
    if location_locator.count() > 0:
        location_locator.first.click()
        page.wait_for_timeout(2000)
        _debug_shot(page, "07_location_selected")
    else:
        print(
            f"Hinweis: Standort '{LOCATION_NAME}' war nicht als klickbares "
            "Element sichtbar - evtl. bereits vorausgewählt oder als reiner "
            "Filter statt als Auswahl-Element umgesetzt."
        )


NEXT_WEEK_LABELS = ["Nächste Woche", "Weiter", "Nächster Termin", ">", "›", "weiter"]


def go_to_next_week(page: Page) -> bool:
    for label in NEXT_WEEK_LABELS:
        locator = page.get_by_role("button", name=label, exact=False)
        if locator.count() > 0 and locator.first.is_enabled():
            locator.first.click()
            page.wait_for_timeout(2000)
            return True

    return False


def read_available_slots(page: Page, category: str) -> list[dict]:
    """Best-effort extraction of visible appointment slots on the current
    week view. UNVERIFIED - the real markup for a free vs. taken slot is
    unknown, so this looks for a time (HH:MM) whose surrounding row/card
    also mentions Albisgütli, and will likely need tuning once the real
    layout is visible in the debug screenshots.
    """
    slots = []

    time_pattern = page.locator("text=/\\b\\d{1,2}:\\d{2}\\b/")

    for i in range(time_pattern.count()):
        element = time_pattern.nth(i)
        text = element.inner_text().strip()

        try:
            container_text = element.locator(
                "xpath=ancestor::*[self::tr or self::li or self::div][1]"
            ).inner_text()
        except Exception:
            container_text = text

        if LOCATION_NAME.lower() not in container_text.lower():
            continue

        slots.append({
            "time": text,
            "date": "unbekannt",
            "category": category,
            "raw": container_text[:200],
        })

    return slots


def check_appointments(halter_nummer: str, geburtsdatum: str, category: str) -> list[dict]:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            login(page, halter_nummer, geburtsdatum)
            open_booking_flow(page, category)

            for week in range(MAX_WEEKS_TO_CHECK):
                _debug_shot(page, f"week_{week:02d}")
                slots = read_available_slots(page, category)

                if slots:
                    return slots

                if not go_to_next_week(page):
                    print(f"Keine 'nächste Woche'-Navigation mehr nach Woche {week}, breche ab.")
                    break

            return []

        except Exception:
            _debug_shot(page, "zz_fatal_error")
            raise
        finally:
            browser.close()
