
import json

import win32pipe
import win32file
import pywintypes

from notifier import notify_deployment_result
from logger import get_logger

log = get_logger()
PIPE_NAME = r'\\.\pipe\DeployNotifierPipe'


def _handle_payload(raw: bytes) -> None:
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        return

    notify_deployment_result(
        payload.get("pipeline_name", "Pipeline"),
        payload.get("display_label", ""),
        payload.get("result", ""),
        payload.get("triggered_by", "Unknown"),
        payload.get("url"),
    )


def main() -> None:

    while True:
        pipe = win32pipe.CreateNamedPipe(
            PIPE_NAME,
            win32pipe.PIPE_ACCESS_INBOUND,
            win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_WAIT,
            1,         
            65536, 65536,
            0, None,
        )
        try:
            win32pipe.ConnectNamedPipe(pipe, None)
            _, data = win32file.ReadFile(pipe, 65536)
            _handle_payload(data)
        except pywintypes.error as e:
            log.warning(f"Pipe hatası: {e}")
        finally:
            try:
                win32file.CloseHandle(pipe)
            except pywintypes.error:
                pass


if __name__ == "__main__":
    main()