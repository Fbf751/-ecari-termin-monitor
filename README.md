# eCARI Termin Monitor

Sucht automatisch alle 10 Minuten nach freien Führerprüfungsterminen (Kategorie
B oder A1) am Standort **Albisgütli** auf dem eCARI-Portal des Strassenverkehrsamts
Zürich und meldet Treffer per Telegram. Keine automatische Buchung.

## Architektur

- **Bot** (`bot/`): Playwright-Skript, das sich bei eCARI einloggt, die gewählte
  Prüfungskategorie und Albisgütli auswählt, sich wochenweise durch den
  Terminkalender klickt und bei einem freien Termin eine Telegram-Nachricht
  schickt. Läuft **nicht** auf Vercel (Playwright braucht einen echten Browser,
  den Vercel-Functions nicht bereitstellen), sondern als geplanter Job in
  **GitHub Actions** (`.github/workflows/monitor.yml`, `cron: */10 * * * *`).
- **Dashboard** (`app/`): Schlanke FastAPI-App ohne Playwright, deployt auf
  Vercel. Zeigt Status an und lässt dich zwischen Kategorie B/A1 wechseln.
  Die Auswahl wird über die GitHub-Contents-API in `config.json` im Repo
  geschrieben; der Bot liest diese Datei bei jedem Lauf.

## Warum das Repo öffentlich sein muss

Private Repos bekommen nur 2'000 Gratis-Minuten/Monat für GitHub Actions –
bei einem Check alle 10 Minuten reicht das nicht. Öffentliche Repos haben
unbegrenzte Gratis-Minuten. Zugangsdaten bleiben davon unberührt: GitHub
Secrets sind auch in öffentlichen Repos verschlüsselt und für niemanden
(auch nicht für Repo-Mitwirkende) einsehbar – nur sichtbar wird der Quellcode.

**Setup:** Repo-Settings → General → Danger Zone → *Change visibility* → Public.

## Einmaliges Setup

### 1. GitHub Actions Secrets (für den Bot)

Repo-Settings → Secrets and variables → Actions → *New repository secret*:

| Name | Wert |
|---|---|
| `ECARI_HALTER_NUMMER` | deine Halter-Nummer |
| `ECARI_GEBURTSDATUM` | Geburtsdatum im Format, das eCARI erwartet (z.B. `TT.MM.JJJJ`) |
| `TELEGRAM_TOKEN` | Bot-Token von [@BotFather](https://t.me/BotFather) (`/newbot`) |
| `TELEGRAM_CHAT_ID` | deine Chat-ID (z.B. via [@userinfobot](https://t.me/userinfobot)) |

### 2. Vercel-Umgebungsvariable (für das Dashboard)

Das Dashboard braucht einen GitHub-Token, um `config.json` im Repo zu
aktualisieren, wenn du B/A1 umschaltest.

1. GitHub → Settings → Developer settings → *Fine-grained personal access token*
   erstellen, Zugriff **nur auf dieses eine Repo**, Berechtigung
   *Contents: Read and write*.
2. In Vercel: Project Settings → Environment Variables →
   `GITHUB_TOKEN` = der Token-Wert.
3. Vercel-Projekt mit diesem Repo verbinden (Root-Verzeichnis: Repo-Root,
   Vercel erkennt `vercel.json` automatisch).

### 3. Repo öffentlich machen

Siehe Abschnitt oben.

## Lokal testen (Dashboard)

```bash
pip install -r requirements.txt
export GITHUB_TOKEN=...   # nur nötig, um /api/settings lokal zu testen
uvicorn app.server:app --host 0.0.0.0 --port 8000
```

Dann `http://127.0.0.1:8000` öffnen.

## Bot manuell auslösen

Statt auf den nächsten Cron-Lauf zu warten: Repo → Actions →
*eCARI Monitor* → *Run workflow*.

## Bekannte Einschränkung: Navigations-Selektoren sind ungetestet

Der Login-Teil (`bot/ecari_client.py: login()`) wurde gegen die echte Seite
getestet. Alles danach – Buchungsflow öffnen, Kategorie/Albisgütli wählen,
durch die Wochen klicken, freie Slots erkennen – wurde **ohne Zugang zu
einem echten eCARI-Konto geschrieben** und ist ein bestmöglicher erster
Entwurf mit mehreren Fallback-Textmustern.

Wenn der erste echte Lauf fehlschlägt (Actions zeigt den Job als "failed"):

1. Im fehlgeschlagenen Workflow-Run das Artifact **debug-screenshots**
   herunterladen – dort liegen Screenshots von jedem Schritt.
2. Anhand der Screenshots sehen, wo die Selektoren nicht zur echten Seite
   passen (`bot/ecari_client.py`: `open_booking_flow`, `go_to_next_week`,
   `read_available_slots`).
3. Selektoren anpassen, pushen, per *Run workflow* erneut testen.

Das ist normalerweise 1–2 Iterationen, bis es zur echten Seite passt.

## Sicherheit

Niemals Halter-Nummer, Geburtsdatum, Telegram-Token oder Chat-ID committen
oder in `workflow_dispatch`-Inputs eintragen. Sie gehören ausschliesslich in
GitHub Actions Secrets.
