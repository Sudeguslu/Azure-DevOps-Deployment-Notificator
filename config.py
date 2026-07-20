import json
import os
import sys
import keyring

KEYRING_SERVICE_NAME = "azure-devops-deploy-notifier"
KEYRING_USERNAME = "pat-token"

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_PATH = os.path.join(BASE_DIR, "config.json")


def load_config() -> dict:
    if not os.path.exists(CONFIG_PATH):
        print(f"ERROR: {CONFIG_PATH} dosen't exist. First you create config file")
        sys.exit(1)

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    required_keys = ["organization", "project", "poll_interval_seconds"]
    missing = [k for k in required_keys if k not in cfg]
    if missing:
        print(f"ERROR: The following fields are missing from config.json: {missing}")
        sys.exit(1)

    return cfg


def get_pat() -> str:
    pat = keyring.get_password(KEYRING_SERVICE_NAME, KEYRING_USERNAME)
    if not pat:
        print(
            "HATA: PAT doesn't exist. First you run this:\n"
            "  python set_pat.py"
        )
        sys.exit(1)
    return pat


def set_pat(pat_value: str) -> None:
    keyring.set_password(KEYRING_SERVICE_NAME, KEYRING_USERNAME, pat_value)
