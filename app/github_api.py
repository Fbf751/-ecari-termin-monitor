import base64
import json
import os

import requests

GITHUB_OWNER = "Fbf751"
GITHUB_REPO = "-ecari-termin-monitor"
CONFIG_PATH_IN_REPO = "config.json"

API_BASE = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents"


def _headers() -> dict:
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        raise RuntimeError("GITHUB_TOKEN ist nicht gesetzt (Vercel-Umgebungsvariable fehlt).")

    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }


def get_config() -> dict:
    response = requests.get(
        f"{API_BASE}/{CONFIG_PATH_IN_REPO}",
        headers=_headers(),
        timeout=15,
    )
    response.raise_for_status()

    data = response.json()
    content = base64.b64decode(data["content"]).decode("utf-8")

    return json.loads(content)


def update_exam_category(category: str) -> dict:
    if category not in ("B", "A1"):
        raise ValueError("Ungültige Kategorie, erlaubt sind 'B' oder 'A1'.")

    get_response = requests.get(
        f"{API_BASE}/{CONFIG_PATH_IN_REPO}",
        headers=_headers(),
        timeout=15,
    )
    get_response.raise_for_status()
    current = get_response.json()
    sha = current["sha"]

    new_content = json.dumps({"exam_category": category}, indent=2) + "\n"
    encoded = base64.b64encode(new_content.encode("utf-8")).decode("utf-8")

    put_response = requests.put(
        f"{API_BASE}/{CONFIG_PATH_IN_REPO}",
        headers=_headers(),
        json={
            "message": f"Einstellung: Prüfungskategorie {category}",
            "content": encoded,
            "sha": sha,
        },
        timeout=15,
    )
    put_response.raise_for_status()

    return {"exam_category": category}
