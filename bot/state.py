import json
from pathlib import Path

DEFAULT_STATE = {"notified_ids": []}


def load_state(path: Path) -> dict:
    if not path.exists():
        return dict(DEFAULT_STATE)

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return dict(DEFAULT_STATE)


def save_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
