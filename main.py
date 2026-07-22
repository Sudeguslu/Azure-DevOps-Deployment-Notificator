import time

from config import load_config, get_pat
from ado_client import get_recent_builds, get_latest_release_deployment, AdoApiError
from state import load_last_build_ids, save_last_build_id
from notifier import notify_deployment_result
from logger import get_logger

log = get_logger()


def _check_build_pipeline(cfg: dict, pat: str, notify_callback) -> None:
    builds = get_recent_builds(
        organization=cfg["organization"],
        project=cfg["project"],
        pat=pat,
        api_version=cfg["api_version"],
    )

    last_ids = load_last_build_ids()

    for build in builds:
        status = build.get("status")
        result = build.get("result")
        if status != "completed" or not result:
            continue

        item_id = build["id"]
        definition = build.get("definition", {})
        pipeline_id = definition.get("id")
        pipeline_name = definition.get("name", "Pipeline")
        display_number = build.get("buildNumber", str(item_id))

        requested_for = build.get("requestedFor", {})
        triggered_by = requested_for.get("displayName", "Unknown")

        commit_hash = build.get("sourceVersion", "")
        commit_message = build.get("sourceVersionMessage", "").replace("\n", " ").replace("\r", "")
        commit_short = commit_hash[:7] if commit_hash else ""
        commit_summary = f" [{commit_short}: {commit_message.strip()[:60]}]" if commit_short else ""

        build_url = (
            f"https://dev.azure.com/{cfg['organization']}/{cfg['project']}"
            f"/_build/results?buildId={item_id}&view=results"
        )

        last_id = last_ids.get(str(pipeline_id))
        if last_id is None or item_id > last_id:
            log.info(f"[{pipeline_name}] Yeni sonuç tespit edildi: {display_number}{commit_summary} -> {result} (tetikleyen: {triggered_by})")
            notify_callback({
                "pipeline_name":pipeline_name,
                "display_label":display_number + commit_summary,
                "result": result,
                "triggered_by": triggered_by,
                "url": build_url,
            })
            save_last_build_id(pipeline_id, item_id)
            last_ids[str(pipeline_id)] = item_id
            
        else:
            log.debug(f"[{pipeline_name}] No changes, last id={item_id} already reported.")


def _check_release_pipeline(cfg: dict, pat: str, notify_callback) -> None:
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
    pipeline_id = cfg["pipeline_id"]

    requested_for = deployment.get("requestedFor", {})
    triggered_by = requested_for.get("displayName", "Bilinmiyor")

    if result not in ("succeeded", "failed", "partiallySucceeded", "canceled", "rejected"):
        return

    display_label = f"{release_name} ({environment_name})" if environment_name else release_name

    release_id = deployment.get("release", {}).get("id")
    environment_ado_id = deployment.get("releaseEnvironment", {}).get("id")
    release_url = (
        f"https://dev.azure.com/{cfg['organization']}/{cfg['project']}"
        f"/_releaseProgress?_a=release-environment-logs"
        f"&releaseId={release_id}&environmentId={environment_ado_id}"
    )

    last_ids = load_last_build_ids()
    last_id = last_ids.get(str(pipeline_id))

    if item_id != last_id:
        log.info(f"[{pipeline_name}] New result: {display_label} -> {result} (triggered by: {triggered_by})")
        notify_callback({
            "pipeline_name": pipeline_name,
            "display_label": display_label,
            "result": result,
            "triggered_by": triggered_by,
            "url": release_url,
        })
        save_last_build_id(pipeline_id, item_id)
    else:
        log.debug(f"[{pipeline_name}] No changes, last id={item_id} already reported.")


def run_once(cfg: dict, pat: str, notify_callback=None) -> None:
    if notify_callback is None:
        def notify_callback(payload):
            notify_deployment_result(
                payload["pipeline_name"],
                payload["display_label"],
                payload["result"],
                payload["triggered_by"],
                payload.get("url"),
            )

    pipeline_type = cfg.get("pipeline_type", "build")

    if pipeline_type == "release":
        _check_release_pipeline(cfg, pat, notify_callback)
    elif pipeline_type == "build":
        _check_build_pipeline(cfg, pat, notify_callback)


def main() -> None:
    cfg = load_config()
    pat = get_pat()
    base_interval = cfg["poll_interval_seconds"]
    consecutive_errors = 0
    max_backoff_seconds = 300

    log.info(f"Deployment is started.")

    while True:
        try:
            run_once(cfg, pat)
            consecutive_errors = 0
            sleep_seconds = base_interval

        except AdoApiError as e:
            consecutive_errors += 1
            sleep_seconds = min(base_interval * (2 ** consecutive_errors), max_backoff_seconds)
            log.warning(f"API hatası")

        except Exception:
            consecutive_errors += 1
            sleep_seconds = min(base_interval * (2 ** consecutive_errors), max_backoff_seconds)
            log.exception(f"Unexpected ERROR")

        time.sleep(sleep_seconds)


if __name__ == "__main__":
    main()