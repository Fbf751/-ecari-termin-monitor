# eCARI Termin Monitor

Sucht automatisch alle 10 Minuten nach freien Führerprüfungsterminen (Kategorie
B oder A1) am Standort **Albisgütli** auf dem eCARI-Portal des Strassenverkehrsamts
Zürich und meldet Treffer per Telegram (Text + Screenshot des Wochenkalenders).
Keine automatische Buchung.

## Architektur

- **Bot** (`bot/`): Playwright-Skript, das sich bei eCARI einloggt, die gewählte
  Prüfungskategorie öffnet (Albisgütli ist im Portal bereits die Standard-Auswahl),
  sich wochenweise durch den Terminkalender klickt und bei einem freien Termin
  eine Telegram-Nachricht samt Screenshot schickt.
- **Läuft lokal, nicht in der Cloud.** portal.stva.zh.ch blockiert Anfragen von
  Cloud-/Datacenter-IPs (bestätigt: GitHub Actions bekam zweimal
  `net::ERR_TIMED_OUT`, während dieselbe Seite von einer normalen Verbindung
  aus sofort lud). Der Bot läuft deshalb als **Windows Scheduled Task** auf
  diesem PC, alle 10 Minuten, siehe unten. `.github/workflows/monitor.yml`
  bleibt nur als manuell auslösbarer (`workflow_dispatch`) Fallback bestehen,
  falls mal ein anderer Cloud-Anbieter getestet werden soll.
- **Dashboard** (`app/`): Schlanke FastAPI-App ohne Playwright, deployt auf
  Vercel. Zeigt Status an und lässt dich zwischen Kategorie B/A1 wechseln.
  Die Auswahl wird über die GitHub-Contents-API in `config.json` im Repo
  geschrieben; der Bot liest diese Datei bei jedem lokalen Lauf.

## Lokal laufen lassen (der eigentliche Betrieb)

### Voraussetzungen (einmalig)

```powershell
pip install -r requirements-bot.txt
python -m playwright install chromium
```

### Zugangsdaten ändern

Alles Sensible steht in `.env` im Repo-Root (per `.gitignore` nie eingecheckt).
Mit Notepad öffnen und bearbeiten:

```powershell
notepad .env
```

Inhalt:

```
ECARI_HALTER_NUMMER=...   # ohne führende Nullen, ohne Punkte (00.010.305.008 -> 10305008)
ECARI_GEBURTSDATUM=...    # TT.MM.JJJJ
TELEGRAM_TOKEN=...        # von @BotFather
TELEGRAM_CHAT_ID=...      # von @userinfobot
```

Speichern reicht – der nächste Lauf (spätestens in 10 Min, oder sofort per
manuellem Start, siehe unten) verwendet automatisch die neuen Werte.

`.env.example` zeigt das erwartete Format ohne echte Werte.

### Automatischer Betrieb (bereits eingerichtet)

Ein Windows Scheduled Task namens **"eCARI Monitor"** ruft alle 10 Minuten
`scripts/run_local.ps1` auf, welches `python -m bot.monitor` ausführt und bei
einem neuen Fund `state/found.json` committet + pusht (damit das Dashboard
den Status auch remote anzeigt).

- Läuft nur, solange du an diesem PC angemeldet bist (nicht zwingend entsperrt).
  War der PC zu einem geplanten Zeitpunkt aus, holt er den verpassten Lauf
  beim nächsten Login nach.
- Prüfen/verwalten: Windows-Suche → "Aufgabenplanung" (Task Scheduler) →
  Task "eCARI Monitor". Oder per PowerShell:
  ```powershell
  Get-ScheduledTaskInfo -TaskName "eCARI Monitor"   # letzter/nächster Lauf
  Start-ScheduledTask -TaskName "eCARI Monitor"     # sofort manuell auslösen
  Disable-ScheduledTask -TaskName "eCARI Monitor"   # pausieren
  Enable-ScheduledTask -TaskName "eCARI Monitor"    # wieder aktivieren
  Unregister-ScheduledTask -TaskName "eCARI Monitor" -Confirm:$false  # löschen
  ```

### Einmalig manuell ausführen (zum Testen)

```powershell
python -m bot.monitor
```

Bei einem Fehler landen Screenshots von jedem Schritt in `debug/` (lokal,
nicht eingecheckt) – hilfreich um zu sehen, wo die Seite nicht mehr zu den
Selektoren in `bot/ecari_client.py` passt, falls eCARI das Layout ändert.

## Dashboard (Vercel) – Prüfungskategorie umschalten

`app/` ist auf Vercel deployt und lässt dich zwischen Kategorie B und A1
wechseln, ohne den PC anzufassen. Ändert `config.json` im Repo über die
GitHub-Contents-API; der nächste lokale Bot-Lauf liest den neuen Wert.

**Hinweis zu A1:** Das eCARI-Portal listet nach dem Login nur die Kategorien
"B" und "A" (nicht "A1" separat) – `CATEGORY_ROW_LABELS` in
`bot/ecari_client.py` mappt "A1" aktuell auf die Zeile "A". Ob/wo sich A1
als Unterauswahl innerhalb der Kategorie A finden lässt, ist noch nicht
verifiziert (dieses Konto wurde nur mit Kategorie B getestet) – bei
Gelegenheit einmal `config.json` auf `"exam_category": "A1"` stellen und
`python -m bot.monitor` laufen lassen, dann `debug/04_booking_flow_opened.png`
ansehen.

### Einmaliges Setup (bereits erledigt für dieses Repo)

1. Repo öffentlich (Settings → Danger Zone → Change visibility) – nötig
   war das eigentlich nur für unbegrenzte Actions-Minuten, die jetzt nicht
   mehr gebraucht werden, aber unproblematisch: Secrets bleiben geschützt.
2. Fine-grained GitHub-Token (nur dieses Repo, *Contents: Read and write*)
   als Vercel-Umgebungsvariable `GITHUB_TOKEN`.
3. Vercel-Projekt mit dem Repo verbunden.

### Lokal testen (Dashboard)

```bash
pip install -r requirements.txt
export GITHUB_TOKEN=...   # nur nötig, um /api/settings lokal zu testen
uvicorn app.server:app --host 0.0.0.0 --port 8000
```

## Sicherheit

Niemals Halter-Nummer, Geburtsdatum, Telegram-Token oder Chat-ID committen
oder in `workflow_dispatch`-Inputs eintragen. Sie gehören ausschliesslich in
die lokale `.env` (für den Bot) bzw. GitHub Actions Secrets (nur falls
`monitor.yml` je wieder mit einem `schedule`-Trigger genutzt wird).
