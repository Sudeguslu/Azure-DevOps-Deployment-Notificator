import time

from config import load_config, get_pat
from ado_client import get_latest_build, get_latest_release_deployment, AdoApiError
from state import load_last_build_id, save_last_build_id
from notifier import notify_deployment_result
from logger import get_logger

log = get_logger()


def _check_build_pipeline(cfg: dict, pat: str, notify_callback) -> None:
    """YAML/Build pipeline için kontrol mantığı."""
    build = get_latest_build(
        organization=cfg["organization"],
        project=cfg["project"],
        pipeline_id=cfg["pipeline_id"],
        pat=pat,
        api_version=cfg["api_version"],
    )

    item_id = build["id"]
    status = build.get("status")
    result = build.get("result")
    display_number = build.get("buildNumber", str(item_id))
    pipeline_name = build.get("definition", {}).get("name", "Pipeline")

    requested_for = build.get("requestedFor", {})
    triggered_by = requested_for.get("displayName", "Bilinmiyor")

    commit_hash = build.get("sourceVersion", "")
    commit_message = build.get("sourceVersionMessage", "").replace("\n", " ").replace("\r", "")
    commit_short = commit_hash[:7] if commit_hash else ""

    if status != "completed" or not result:
        return

    commit_summary = f" [{commit_short}: {commit_message.strip()[:60]}]" if commit_short else ""
    _notify_if_new(item_id, pipeline_name, display_number + commit_summary, result, triggered_by, notify_callback)


def _check_release_pipeline(cfg: dict, pat: str, notify_callback) -> None:
    """Classic Release pipeline için kontrol mantığı."""
    deployment = get_latest_release_deployment(
        organization=cfg["organization"],
        project=cfg["project"],
        definition_id=cfg["pipeline_id"],
        pat=pat,
        environment_id=cfg.get("environment_id"),
        api_version=cfg["api_version"],
    )

    item_id = deployment["id"]
    result = deployment.get("deploymentStatus")
    release_name = deployment.get("release", {}).get("name", str(item_id))
    pipeline_name = deployment.get("releaseDefinition", {}).get("name", "Release Pipeline")
    environment_name = deployment.get("releaseEnvironment", {}).get("name", "")

    requested_for = deployment.get("requestedFor", {})
    triggered_by = requested_for.get("displayName", "Bilinmiyor")

    if result not in ("succeeded", "failed", "partiallySucceeded", "canceled", "rejected"):
        return

    display_label = f"{release_name} ({environment_name})" if environment_name else release_name
    _notify_if_new(item_id, pipeline_name, display_label, result, triggered_by, notify_callback)


def _notify_if_new(item_id: int, pipeline_name: str, display_label: str,
                    result: str, triggered_by: str, notify_callback) -> None:
    """Build ve Release akışının ortak son adımı: state karşılaştırması + bildirim."""
    last_id = load_last_build_id()

    if item_id != last_id:
        log.info(f"[{pipeline_name}] Yeni sonuç tespit edildi: {display_label} -> {result} (tetikleyen: {triggered_by})")
        notify_callback({
            "pipeline_name": pipeline_name,
            "display_label": display_label,
            "result": result,
            "triggered_by": triggered_by,
        })
        save_last_build_id(item_id)
    else:
        log.debug(f"[{pipeline_name}] Değişiklik yok, son id={item_id} zaten bildirilmiş.")


def run_once(cfg: dict, pat: str, notify_callback=None) -> None:
    if notify_callback is None:
        # Varsayılan davranış: doğrudan toast göster (mevcut console-app modu)
        def notify_callback(payload):
            notify_deployment_result(
                payload["pipeline_name"],
                payload["display_label"],
                payload["result"],
                payload["triggered_by"],
            )

    pipeline_type = cfg.get("pipeline_type", "build")

    if pipeline_type == "release":
        _check_release_pipeline(cfg, pat, notify_callback)
    elif pipeline_type == "build":
        _check_build_pipeline(cfg, pat, notify_callback)
    else:
        raise ValueError(
            f"Bilinmeyen pipeline_type: '{cfg.get('pipeline_type')}'. "
            "config.json'da 'build' veya 'release' olmalı."
        )


def main() -> None:
    cfg = load_config()
    pat = get_pat()
    base_interval = cfg["poll_interval_seconds"]
    consecutive_errors = 0
    max_backoff_seconds = 300

    log.info(f"Deployment notifier başlatıldı. Her {base_interval} saniyede bir kontrol edilecek.")

    while True:
        try:
            run_once(cfg, pat)
            consecutive_errors = 0
            sleep_seconds = base_interval

        except AdoApiError as e:
            consecutive_errors += 1
            sleep_seconds = min(base_interval * (2 ** consecutive_errors), max_backoff_seconds)
            log.warning(f"API hatası ({consecutive_errors}. art arda): {e} -- {sleep_seconds}s sonra tekrar denenecek")

        except Exception:
            consecutive_errors += 1
            sleep_seconds = min(base_interval * (2 ** consecutive_errors), max_backoff_seconds)
            log.exception(f"Beklenmeyen hata -- {sleep_seconds}s sonra tekrar denenecek")

        time.sleep(sleep_seconds)


if __name__ == "__main__":
    main()