import json
import os
import sys
from pathlib import Path

from bot.ecari_client import check_appointments
from bot.notify import format_slot_message, send_telegram
from bot.state import load_state, save_state

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config.json"
STATE_PATH = ROOT / "state" / "found.json"


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        return {"exam_category": "B"}
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def main() -> int:
    halter_nummer = os.environ.get("ECARI_HALTER_NUMMER", "")
    geburtsdatum = os.environ.get("ECARI_GEBURTSDATUM", "")
    telegram_token = os.environ.get("TELEGRAM_TOKEN", "")
    telegram_chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")

    if not halter_nummer or not geburtsdatum:
        print("ECARI_HALTER_NUMMER / ECARI_GEBURTSDATUM fehlen (GitHub Secrets prüfen).")
        return 1

    config = load_config()
    category = config.get("exam_category", "B")
    print(f"Prüfe Termine für Kategorie {category} in Albisgütli...")

    slots = check_appointments(halter_nummer, geburtsdatum, category)
    print(f"{len(slots)} passende(r) Slot(s) auf der Seite gefunden.")

    state = load_state(STATE_PATH)
    notified_ids = set(state.get("notified_ids", []))

    new_slots = []
    for slot in slots:
        slot_id = f"{category}|{slot.get('date')}|{slot.get('time')}"
        if slot_id in notified_ids:
            continue
        notified_ids.add(slot_id)
        new_slots.append(slot)

    if new_slots:
        print(f"{len(new_slots)} neue(r) Termin(e) - sende Telegram-Benachrichtigung.")
        send_telegram(telegram_token, telegram_chat_id, format_slot_message(new_slots))
    else:
        print("Keine neuen Termine seit dem letzten Lauf.")

    state["notified_ids"] = sorted(notified_ids)
    save_state(STATE_PATH, state)

    return 0


if __name__ == "__main__":
    sys.exit(main())
