import win32serviceutil
import win32service
import win32event
import servicemanager
import win32pipe
import win32file
import json

from config import load_config, get_pat
from main import run_once
from logger import get_logger

log = get_logger()
PIPE_NAME = r'\\.\pipe\DeployNotifierPipe'


def send_to_pipe(payload: dict) -> None:
    """Named pipe üzerinden user-session notifier'a mesaj gönderir."""
    try:
        handle = win32file.CreateFile(
            PIPE_NAME,
            win32file.GENERIC_WRITE,
            0, None,
            win32file.OPEN_EXISTING,
            0, None
        )
        win32file.WriteFile(handle, json.dumps(payload).encode("utf-8"))
        win32file.CloseHandle(handle)
        log.info(f"Bildirim pipe'a gönderildi: {payload}")
    except Exception as e:
        log.warning(f"Notifier pipe'a bağlanılamadı (kullanıcı oturumu açık olmayabilir): {e}")


class DeployNotifierService(win32serviceutil.ServiceFramework):
    _svc_name_ = "DeployNotifierService"
    _svc_display_name_ = "Azure DevOps Deploy Notifier"
    _svc_description_ = "Azure DevOps pipeline sonuçlarını izler, kullanıcıya bildirim gönderir."

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.running = True

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        self.running = False

    def SvcDoRun(self):
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        self.main_loop()

    def main_loop(self):
        cfg = load_config()
        pat = get_pat()
        interval = cfg["poll_interval_seconds"]

        log.info(f"DeployNotifierService başladı. Her {interval} saniyede bir kontrol edilecek.")

        while self.running:
            try:
                run_once(cfg, pat, notify_callback=send_to_pipe)
            except Exception:
                log.exception("Servis döngüsünde hata")

            result = win32event.WaitForSingleObject(self.stop_event, interval * 1000)
            if result == win32event.WAIT_OBJECT_0:
                break


if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(DeployNotifierService)