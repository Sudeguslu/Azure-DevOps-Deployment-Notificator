import json
import os

STATE_PATH = os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
    "DeployNotifier",
    "state.json",
)


def load_last_build_id() -> int | None:
    if not os.path.exists(STATE_PATH):
        return None
    try:
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("last_build_id")
    except (json.JSONDecodeError, OSError):
        # Dosya bozuksa sıfırdan başla, servisi durdurma
        return None


def save_last_build_id(build_id: int) -> None:
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump({"last_build_id": build_id}, f)
