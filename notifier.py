from win11toast import toast


def notify_deployment_result(pipeline_name: str, build_number: str, result: str,
                              triggered_by: str = "Bilinmiyor") -> None:
    if result == "succeeded":
        title = "Deployment succeeded"
    elif result == "failed":
        title = "Deployment failed"

    message = f"{pipeline_name} — build{build_number}\nTriggered by {triggered_by}"

    toast(title, message, duration="short")
