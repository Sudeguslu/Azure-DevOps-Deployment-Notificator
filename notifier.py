from win11toast import toast


def notify_deployment_result(pipeline_name: str, build_number: str, result: str,
                              triggered_by: str = "Bilinmiyor", url: str = None) -> None:
    titles = {
        "succeeded": "Deployment succeeded",
        "failed": "Deployment failed",
        "partiallySucceeded": "Deployment partially succeeded",
        "canceled": "Deployment canceled",
        "rejected": "Deployment rejected",
    }
    title = titles.get(result, f"Deployment {result}")
    message = f"{pipeline_name} — build {build_number}\nTriggered by {triggered_by}"

    # URL verilmişse tıklanınca o adresi tarayıcıda açar
    toast(title, message, duration="short", on_click=url if url else None)