import win32pipe
import win32file
import json
import pywintypes
from notifier import notify_deployment_result
from logger import get_logger

log = get_logger()
PIPE_NAME = r'\\.\pipe\DeployNotifierPipe'


def run_notifier():
    log.info("User notifier başlatıldı, servisten gelecek mesajlar bekleniyor...")
    while True:
        try:
            pipe = win32pipe.CreateNamedPipe(
                PIPE_NAME,
                win32pipe.PIPE_ACCESS_INBOUND,
                win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_WAIT,
                1, 65536, 65536, 0, None
            )
            win32pipe.ConnectNamedPipe(pipe, None)
            result, data = win32file.ReadFile(pipe, 65536)
            payload = json.loads(data.decode("utf-8"))

            log.info(f"Servisten mesaj alındı: {payload}")

            notify_deployment_result(
                payload["pipeline_name"],
                payload["display_label"],
                payload["result"],
                payload["triggered_by"],
            )
            win32file.CloseHandle(pipe)
        except pywintypes.error as e:
            log.warning(f"Pipe hatası: {e}")
            continue
        except Exception:
            log.exception("Notifier döngüsünde beklenmeyen hata")


if __name__ == "__main__":
    run_notifier()