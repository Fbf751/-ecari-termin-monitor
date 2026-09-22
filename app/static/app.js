const GITHUB_OWNER = "Fbf751";
const GITHUB_REPO = "-ecari-termin-monitor";
const RAW_BASE = `https://raw.githubusercontent.com/${GITHUB_OWNER}/${GITHUB_REPO}/main`;
const RUNS_URL = `https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/actions/workflows/monitor.yml/runs?per_page=1`;

const settingsForm = document.getElementById("settings-form");
const saveButton = document.getElementById("save-button");
const settingsResult = document.getElementById("settings-result");
const statusText = document.getElementById("status-text");

function escapeHtml(v) {
  return String(v).replaceAll("&", "&amp;").replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#039;");
}

function showSettingsResult(message, type = "success") {
  settingsResult.className = `result ${type}`;
  settingsResult.textContent = message;
  settingsResult.classList.remove("hidden");
}

async function loadCurrentCategory() {
  try {
    const r = await fetch("/api/settings");
    const d = await r.json();
    if (!d.success) throw new Error(d.error || "Einstellung konnte nicht geladen werden.");

    const radio = settingsForm.querySelector(`input[value="${d.exam_category}"]`);
    if (radio) radio.checked = true;
  } catch (err) {
    showSettingsResult(err.message, "error");
  }
}

async function loadStatus() {
  const parts = [];

  try {
    const r = await fetch(`${RAW_BASE}/state/found.json`, { cache: "no-store" });
    const d = await r.json();
    const count = (d.notified_ids || []).length;
    parts.push(count > 0
      ? `📬 Bisher ${count} gemeldete(r) Termin-Slot(s).`
      : "Noch keine passenden Termine gefunden.");
  } catch {
    parts.push("Status konnte nicht geladen werden.");
  }

  try {
    const r = await fetch(RUNS_URL);
    const d = await r.json();
    const run = (d.workflow_runs || [])[0];
    if (run) {
      const when = new Date(run.run_started_at).toLocaleString("de-CH");
      const icon = run.conclusion === "success" ? "🟢" : run.conclusion === "failure" ? "🔴" : "🟡";
      parts.push(`${icon} Letzter Bot-Lauf: ${when} (${run.status})`);
    }
  } catch {
    // GitHub API rate limit oder nicht erreichbar - kein Blocker für die Seite.
  }

  statusText.innerHTML = parts.map(escapeHtml).join("<br>");
}

settingsForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  saveButton.disabled = true;
  saveButton.textContent = "Speichert...";

  try {
    const r = await fetch("/api/settings", { method: "POST", body: new FormData(settingsForm) });
    const d = await r.json();
    if (!d.success) throw new Error(d.error || "Speichern fehlgeschlagen.");
    showSettingsResult(`Gespeichert: Kategorie ${d.exam_category}. Der nächste Bot-Lauf verwendet diese Einstellung.`);
  } catch (err) {
    showSettingsResult(err.message, "error");
  } finally {
    saveButton.disabled = false;
    saveButton.textContent = "Speichern";
  }
});

loadCurrentCategory();
loadStatus();
