# eCARI Termin Monitor

Sucht automatisch alle 10 Minuten nach freien Führerprüfungsterminen (Kategorie
B oder A1) am Standort **Albisgütli** auf dem eCARI-Portal des Strassenverkehrsamts
Zürich und meldet Treffer per Telegram (Text + Screenshot des Wochenkalenders).
Keine automatische Buchung.

## Architektur

Läuft komplett lokal auf diesem PC, nichts in der Cloud:

- **Bot** (`bot/`): Playwright-Skript, das sich bei eCARI einloggt, die gewählte
  Prüfungskategorie öffnet (Albisgütli ist im Portal bereits die Standard-Auswahl),
  sich wochenweise durch den Terminkalender klickt und bei einem freien Termin
  eine Telegram-Nachricht samt Screenshot schickt.
- **Warum lokal:** portal.stva.zh.ch blockiert Anfragen von Cloud-/Datacenter-IPs
  (bestätigt: GitHub Actions bekam zweimal `net::ERR_TIMED_OUT`, während dieselbe
  Seite von einer normalen Verbindung aus sofort lud). Ein Windows Scheduled Task
  ruft den Bot deshalb alle 10 Minuten direkt auf diesem PC auf.
- Kein Dashboard, kein Cloud-Hosting, kein API-Token mehr nötig – Zugangsdaten
  liegen in `.env`, die Prüfungskategorie in `config.json`, beide werden direkt
  mit einem Texteditor bearbeitet (siehe unten bzw. die Desktop-Verknüpfungen).

## Voraussetzungen (einmalig)

```powershell
pip install -r requirements.txt
python -m playwright install chromium
```

## Zugangsdaten ändern

Alles Sensible steht in `.env` im Repo-Root (per `.gitignore` nie eingecheckt).

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
manuellem Start) verwendet automatisch die neuen Werte. `.env.example` zeigt
das Format ohne echte Werte.

## Prüfungskategorie wechseln (B / A1)

```powershell
notepad config.json
```

```json
{ "exam_category": "B" }
```

Wert auf `"B"` oder `"A1"` setzen, speichern, fertig – oder einfach die
Desktop-Verknüpfung **"3. Kategorie wechseln"** benutzen.

**Hinweis zu A1:** Das eCARI-Portal listet nach dem Login nur die Kategorien
"B" und "A" (nicht "A1" separat) – `CATEGORY_ROW_LABELS` in
`bot/ecari_client.py` mappt "A1" aktuell auf die Zeile "A". Ob/wo sich A1
als Unterauswahl innerhalb der Kategorie A finden lässt, ist noch nicht
verifiziert (bisher nur mit Kategorie B getestet) – nach dem Umstellen einmal
`python -m bot.monitor` laufen lassen und `debug/04_booking_flow_opened.png`
ansehen, um zu sehen, was die Seite für A1 tatsächlich zeigt.

## Automatischer Betrieb (bereits eingerichtet)

Ein Windows Scheduled Task namens **"eCARI Monitor"** ruft alle 10 Minuten
`scripts/run_local.ps1` auf, welches `python -m bot.monitor` ausführt und bei
einem neuen Fund `state/found.json` committet + pusht (als Backup/Verlauf,
rein optional – der Bot selbst braucht das nicht).

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

## Desktop-Verknüpfungen

Ordner **"eCARI Monitor"** auf dem Desktop:

1. **Jetzt prüfen** – sofortiger Check mit sichtbarem Ergebnis-Fenster
2. **Zugangsdaten bearbeiten** – öffnet `.env`
3. **Kategorie wechseln** – öffnet `config.json`
4. **Debug-Screenshots öffnen** – letzter Lauf Schritt für Schritt

## Einmalig manuell ausführen (zum Testen)

```powershell
python -m bot.monitor
```

Bei einem Fehler landen Screenshots von jedem Schritt in `debug/` (lokal,
nicht eingecheckt) – hilfreich um zu sehen, wo die Seite nicht mehr zu den
Selektoren in `bot/ecari_client.py` passt, falls eCARI das Layout ändert.

## Sicherheit

Niemals Halter-Nummer, Geburtsdatum, Telegram-Token oder Chat-ID committen.
Sie gehören ausschliesslich in die lokale `.env`.
