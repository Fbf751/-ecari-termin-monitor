# CLAUDE.md

Guidance for Claude Code when working in this repo.

## What this is

A bot that checks portal.stva.zh.ch (eCARI, Strassenverkehrsamt Zürich) for
free Führerprüfung slots at **Albisgütli** for a chosen category (B or A1),
and sends a Telegram message + screenshot when it finds one. No automatic
booking - notification only.

## Architecture: runs 100% locally. Do not try to move it to the cloud again.

This was already attempted and reverted twice in this repo's history -
**don't redo that work**:

1. **portal.stva.zh.ch blocks datacenter/cloud IPs.** Confirmed via two live
   GitHub Actions runs, both `net::ERR_TIMED_OUT` at the exact same
   `page.goto()` call, while the same page loaded instantly from a normal
   (non-datacenter) connection. This almost certainly rules out GitHub
   Actions, and very likely most other free-tier CI/cloud hosts too (they
   mostly sit on the same well-known blocked ranges). If asked to make this
   "run in the cloud" or "run for free somewhere", **lead with this
   constraint** rather than re-discovering it.
2. **There used to be a Vercel-hosted dashboard** (`app/` + `vercel.json`)
   that let you toggle B/A1 remotely via the GitHub Contents API. It was
   deliberately removed once everything else also moved local - a whole
   deploy + API round-trip wasn't worth it for a single local toggle.
   Switching category is now just editing `config.json` directly.

So: the bot runs via a **Windows Scheduled Task** ("eCARI Monitor", every 10
min) that calls `scripts/run_local.ps1`, entirely on the user's own PC. See
README.md for the full setup/management commands.

## Layout

- `bot/ecari_client.py` - Playwright site navigation (login, category
  selection, week-by-week click-through, slot detection). Selectors here
  were calibrated against a real logged-in session - see inline comments
  before changing them blind.
- `bot/monitor.py` - entrypoint (`python -m bot.monitor`), reads
  `config.json` + `.env`, dedupes against `state/found.json`, notifies.
- `bot/notify.py` - Telegram send (text + photo).
- `config.json` - `{"exam_category": "B"}` or `"A1"` - committed to git,
  edited directly (desktop shortcut "3. Kategorie wechseln").
- `.env` - **never committed** (gitignored). Holds
  `ECARI_HALTER_NUMMER`, `ECARI_GEBURTSDATUM`, `TELEGRAM_TOKEN`,
  `TELEGRAM_CHAT_ID`. `.env.example` shows the format.
- `state/found.json` - dedupe list of already-notified slot IDs, committed
  as an optional off-site backup/history (not required for the bot to
  function).
- `scripts/run_local.ps1` - what the Scheduled Task actually runs.
- `scripts/run_now.ps1` - manual run with a visible console window
  (desktop shortcut "1. Jetzt prüfen").
- `debug/` - gitignored, screenshots from the last run (every navigation
  step, plus a "zz_fatal_error" shot on any crash). First thing to check
  when the site's layout has drifted from what the selectors expect.

## Known site quirks (as of the last real calibration run)

- Login button's accessible name is **"Login"**, not "Anmelden"/"Weiter".
- Halter-Nummer must be entered **without leading zeros and without dots**
  (`00.010.305.008` -> `10305008`) - the login page itself states this.
- After login, category rows ("B", "A" - not "A1") appear in an
  "Anmeldung zur Prüfung" table with an "Auswählen" link *only if you don't
  already have a booking for that category*. If you do, that category's row
  disappears from this table but the same letter can still appear elsewhere
  (in "Bestehende Termine"), so `open_booking_flow()` scans *all* text
  matches for the one actually paired with an "Auswählen" link, and raises
  `AlreadyBookedError` (handled gracefully, not a crash) if none qualifies
  and a "Bestehende Termine" section exists.
- **"A1" is not a real category in the portal - only "B" and "A" exist.**
  `CATEGORY_ROW_LABELS` maps "A1" -> "A" as a guess. Whether/where an A1
  sub-selection happens after choosing "A" is **still unverified** - this
  account has only been tested with category B. If asked to work on A1,
  check `debug/04_booking_flow_opened.png` after a real run first.
- "Prüfungsort" is a `<select>` that already defaults to Albisgütli - no
  click needed, just `select_option()` defensively.
- Week view marks empty days with the exact string "Keine Termine frei".
  The "Termine verfügbar bis: DD.MM.YYYY" cutoff line matches the same
  date regex as weekday headers - explicitly filtered out in
  `read_available_slots()`, don't reintroduce that false positive.

## Security

Never commit real values for `ECARI_HALTER_NUMMER`, `ECARI_GEBURTSDATUM`,
`TELEGRAM_TOKEN`, or `TELEGRAM_CHAT_ID`. They belong only in the local
`.env`, which is gitignored.

## Repo history note

A duplicate/earlier attempt at this same bot (`Fbf751/Pr-fungsbot`) existed
and was deleted during a cleanup pass. This repo is the one and only
surviving version - don't recreate the old one or assume it still exists.
