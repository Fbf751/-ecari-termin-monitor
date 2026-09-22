import requests

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


def send_telegram(token: str, chat_id: str, text: str) -> bool:
    if not token or not chat_id:
        print("Telegram nicht konfiguriert, überspringe Benachrichtigung.")
        return False

    response = requests.post(
        TELEGRAM_API.format(token=token),
        json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        },
        timeout=15,
    )

    if not response.ok:
        print("Telegram-Versand fehlgeschlagen:", response.status_code, response.text)
        return False

    return True


def format_slot_message(slots: list[dict]) -> str:
    lines = ["🚗 <b>Freier Prüfungstermin in Albisgütli gefunden!</b>", ""]

    for slot in slots:
        lines.append(f"• {slot['date']} {slot['time']} – Kategorie {slot['category']}")

    lines.append("")
    lines.append("Jetzt buchen: https://portal.stva.zh.ch/ecari-dispoweb/ui/app/init/#/conduite/prive/login")

    return "\n".join(lines)
