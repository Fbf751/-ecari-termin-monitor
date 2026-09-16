# eCARI Termin Monitor

Mobile Weboberfläche und sicherer Testmodus für den späteren eCARI-Adapter.

## Aktueller Stand

- Mobile Oberfläche vorhanden.
- Testtermine werden angezeigt.
- Keine automatische Buchung.
- Zugangsdaten werden nicht in GitHub-Dateien gespeichert.
- Der aktuelle Monitor ruft absichtlich noch NICHT eCARI auf.
- Für den echten Betrieb muss ein sicherer Server mit Playwright ergänzt werden.

## Lokal testen

```bash
pip install -r requirements.txt
uvicorn app.server:app --host 0.0.0.0 --port 8000
```

Dann `http://127.0.0.1:8000` öffnen.

## Sicherheit

Niemals Halter-Nummer, Geburtsdatum, Telegram-Token oder Chat-ID committen.
Niemals echte Zugangsdaten in GitHub Actions `workflow_dispatch`-Inputs eintragen.
