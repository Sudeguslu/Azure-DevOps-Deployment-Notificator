
import base64
import requests

_session = requests.Session()

class AdoApiError(Exception):
    pass


def _build_auth_header(pat: str) -> dict:
    token = base64.b64encode(f":{pat}".encode("utf-8")).decode("utf-8")
    return {"Authorization": f"Basic {token}"}


def _get(url: str, pat: str, timeout: int) -> dict:
    try:
        response = _session.get(url, headers=_build_auth_header(pat), timeout=timeout)
    except requests.exceptions.RequestException as e:
        raise AdoApiError(f"API isteği başarısız: {e}") from e

    if response.status_code == 401:
        raise AdoApiError("Yetkilendirme hatası (401). PAT geçersiz veya süresi dolmuş olabilir.")
    if response.status_code != 200:
        raise AdoApiError(f"Beklenmeyen HTTP durumu: {response.status_code} - {response.text[:200]}")

    return response.json()


def get_latest_build(organization: str, project: str, pipeline_id: int,
                      pat: str, api_version: str = "7.1", timeout: int = 15) -> dict:
    url = (
        f"https://dev.azure.com/{organization}/{project}/_apis/build/builds"
        f"?definitions={pipeline_id}&$top=1&queryOrder=finishTimeDescending"
        f"&api-version={api_version}"
    )

    data = _get(url, pat, timeout)
    builds = data.get("value", [])
    if not builds:
        raise AdoApiError("Bu pipeline için hiç build bulunamadı. pipeline_id doğru mu?")

    return builds[0]


def get_latest_release_deployment(organization: str, project: str, definition_id: int,
                                   pat: str, environment_id: int | None = None,
                                   api_version: str = "7.1", timeout: int = 15) -> dict:
    url = (
        f"https://vsrm.dev.azure.com/{organization}/{project}/_apis/release/deployments"
        f"?definitionId={definition_id}&$top=1&queryOrder=descending"
        f"&api-version={api_version}"
    )
    if environment_id is not None:
        url += f"&definitionEnvironmentId={environment_id}"

    data = _get(url, pat, timeout)
    deployments = data.get("value", [])
    if not deployments:
        raise AdoApiError("Bu release pipeline için hiç deployment bulunamadı. definition_id doğru mu?")

    return deployments[0]
