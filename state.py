import json
import os

STATE_PATH = os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
    "DeployNotifier",
    "state.json",
)


def load_last_build_ids() -> dict:
    if not os.path.exists(STATE_PATH):
        return {}
    try:
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("last_build_ids", {})
    except (json.JSONDecodeError, OSError):
        return {}


def save_last_build_id(pipeline_id: int, build_id: int) -> None:
    ids = load_last_build_ids()
    ids[str(pipeline_id)] = build_id
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump({"last_build_ids": ids}, f)