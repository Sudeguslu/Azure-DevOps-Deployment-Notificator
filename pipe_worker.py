
import time

from config import load_config, get_pat
from main import run_once
from logger import get_logger
from service import send_to_pipe

log = get_logger()


def main() -> None:
    cfg = load_config()
    pat = get_pat()
    interval = cfg["poll_interval_seconds"]

    log.info("Pipe worker started.")

    while True:
        try:
            run_once(cfg, pat, notify_callback=send_to_pipe)
        except Exception:
            log.exception("Worker loop error")

        time.sleep(interval)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log.info("Pipe worker durduruldu (stop sinyali alindi).")