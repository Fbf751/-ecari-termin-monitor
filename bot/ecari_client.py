from datetime import datetime
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

ECARI_URL = (
    "https://portal.stva.zh.ch/"
    "ecari-dispoweb/ui/app/init/"
    "#/conduite/prive/login"
)

LOCATION_NAME = "Albisgütli"

# The post-login page lists rows like "Fahrprüfung | B | Auswählen" -
# confirmed against a real session. The portal only lists the broad "A"
# category, not "A1" specifically; the A1 sub-selection (if any) presumably
# happens on the page that opens after clicking "Auswählen" for "A" - this
# still needs to be confirmed against a real run with category A1 selected.
CATEGORY_ROW_LABELS = {
    "B": "B",
    "A1": "A",
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


def _debug_shot(page: Page, label: str) -> Path | None:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%H%M%S")
    path = DEBUG_DIR / f"{ts}_{label}.png"
    try:
        page.screenshot(path=str(path), full_page=True)
    except Exception as e:
        print(f"Screenshot fehlgeschlagen ({label}):", e)
        return None
    return path


def login(page: Page, halter_nummer: str, geburtsdatum: str) -> None:
    page.goto(ECARI_URL, wait_until="commit", timeout=60000)
    page.wait_for_timeout(5000)
    _debug_shot(page, "01_login_page")

    inputs = page.locator("input")
    if inputs.count() < 2:
        raise EcariNavigationError("Login-Eingabefelder wurden nicht gefunden.")

    inputs.nth(0).fill(halter_nummer)
    inputs.nth(1).fill(geburtsdatum)

    login_button = page.get_by_role("button", name="Login", exact=True)
    if login_button.count() == 0:
        login_button = page.get_by_role("button", name="Anmelden", exact=True)
    if login_button.count() == 0:
        login_button = page.get_by_role("button", name="Weiter", exact=True)
    if login_button.count() == 0:
        raise EcariNavigationError("Login-Schaltfläche wurde nicht gefunden.")

    login_button.first.click()
    page.wait_for_timeout(5000)
    _debug_shot(page, "02_after_login")


def open_booking_flow(page: Page, category: str) -> None:
    """Click "Auswählen" on the post-login table row matching the given
    exam category ("B" or "A1" - "A1" maps to the row labelled just "A",
    see CATEGORY_ROW_LABELS). Confirmed against a real session: this lands
    directly on the "Neuer Termin" week view, with a "Prüfungsort" <select>
    that already defaults to Albisgütli.
    """
    row_label = CATEGORY_ROW_LABELS.get(category, category)

    category_cell = page.get_by_text(row_label, exact=True)
    if category_cell.count() == 0:
        _debug_shot(page, "03_category_row_not_found")
        raise EcariNavigationError(f"Kategorie-Zeile '{row_label}' wurde nicht gefunden.")

    row = category_cell.first.locator("xpath=ancestor::tr[1]")
    select_link = row.get_by_text("Auswählen", exact=True)
    if select_link.count() == 0:
        _debug_shot(page, "03_select_link_not_found")
        raise EcariNavigationError("'Auswählen'-Link in der Kategorie-Zeile wurde nicht gefunden.")

    select_link.first.click()
    page.wait_for_timeout(3000)
    _debug_shot(page, "04_booking_flow_opened")

    location_select = page.locator("select")
    if location_select.count() > 0:
        try:
            location_select.first.select_option(label=LOCATION_NAME)
            page.wait_for_timeout(1500)
        except Exception as e:
            print(f"Hinweis: Standort-Auswahl '{LOCATION_NAME}' fehlgeschlagen ({e}) - evtl. bereits vorausgewählt.")
    else:
        print("Hinweis: Kein <select> für den Prüfungsort gefunden - evtl. hat sich das Seitenlayout geändert.")

    _debug_shot(page, "05_location_confirmed")


NEXT_WEEK_LABELS = ["Nächste Woche", "Weiter", "Nächster Termin", ">", "›", "weiter"]


def go_to_next_week(page: Page) -> bool:
    for label in NEXT_WEEK_LABELS:
        locator = page.get_by_role("button", name=label, exact=False)
        if locator.count() > 0 and locator.first.is_enabled():
            locator.first.click()
            page.wait_for_timeout(2000)
            return True

    return False


NO_SLOTS_TEXT = "Keine Termine frei"


def read_available_slots(page: Page, category: str) -> list[dict]:
    """Extract appointment slots from the current week view. Confirmed
    against a real session: each weekday column has a "DD.MM.YYYY" date
    header, and shows "Keine Termine frei" when empty. What a column looks
    like when a slot IS available is still unconfirmed (this account had no
    free slots during calibration) - this treats any column that does NOT
    say "Keine Termine frei" as a hit, and reports whatever text/times are
    in it. If real slots turn out to look different than expected, the
    Telegram message's "raw" text will still show what was actually there.
    """
    slots = []

    date_headers = page.locator("text=/\\b\\d{2}\\.\\d{2}\\.\\d{4}\\b/")

    for i in range(date_headers.count()):
        date_el = date_headers.nth(i)
        date_text = date_el.inner_text().strip()

        try:
            column = date_el.locator("xpath=ancestor::*[self::div or self::td or self::li][1]")
            column_text = column.inner_text()
        except Exception:
            column_text = date_text

        if "Termine verfügbar" in column_text:
            # The "Termine verfügbar bis: DD.MM.YYYY" cutoff line also
            # matches the date pattern - it's not a weekday column.
            continue

        if NO_SLOTS_TEXT in column_text:
            continue

        times = column.locator("text=/\\b\\d{1,2}:\\d{2}\\b/")
        time_texts = [times.nth(j).inner_text().strip() for j in range(times.count())]

        slots.append({
            "time": ", ".join(time_texts) if time_texts else "siehe raw",
            "date": date_text,
            "category": category,
            "raw": column_text[:300],
        })

    return slots


def check_appointments(halter_nummer: str, geburtsdatum: str, category: str) -> dict:
    """Returns {"slots": [...], "screenshot": Path | None} - the screenshot
    is the exact week view the slots were read from, for attaching to the
    Telegram notification as visual proof.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            login(page, halter_nummer, geburtsdatum)
            open_booking_flow(page, category)

            for week in range(MAX_WEEKS_TO_CHECK):
                shot_path = _debug_shot(page, f"week_{week:02d}")
                slots = read_available_slots(page, category)

                if slots:
                    return {"slots": slots, "screenshot": shot_path}

                if not go_to_next_week(page):
                    print(f"Keine 'nächste Woche'-Navigation mehr nach Woche {week}, breche ab.")
                    break

            return {"slots": [], "screenshot": None}

        except Exception:
            _debug_shot(page, "zz_fatal_error")
            raise
        finally:
            browser.close()
