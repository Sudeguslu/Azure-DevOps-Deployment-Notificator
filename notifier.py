from win11toast import toast


def notify_deployment_result(pipeline_name: str, build_number: str, result: str,
                              triggered_by: str = "Bilinmiyor") -> None:
    titles = {
        "succeeded": "Deployment succeeded",
        "failed": "Deployment failed",
        "partiallySucceeded": "Deployment partially succeeded",
        "canceled": "Deployment canceled",
        "rejected": "Deployment rejected",
    }
    title = titles.get(result, f"Deployment {result}")
    message = f"{pipeline_name} — build {build_number}\nTriggered by {triggered_by}"
    toast(title, message, duration="short")
