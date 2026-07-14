
import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
    "DeployNotifier",
)
LOG_PATH = os.path.join(LOG_DIR, "deploy_notifier.log")


def get_logger() -> logging.Logger:
    os.makedirs(LOG_DIR, exist_ok=True)

    logger = logging.getLogger("deploy_notifier")
    logger.setLevel(logging.INFO)

    # main() birden fazla kez çağrılırsa (örn. testlerde) handler'ın
    # tekrar tekrar eklenip aynı satırın birden fazla yazılmasını önler
    if not logger.handlers:
        handler = RotatingFileHandler(
            LOG_PATH, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
        )
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        # Geliştirme sırasında terminalde de görmek için ayrıca konsola da yaz.
        # İleride gerçek servise geçince bu satır kaldırılabilir.
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger
