# Azure DevOps Deployment Notificator

A lightweight Windows tool that watches your Azure DevOps pipelines and notifies you the moment a deployment finishes — no more tabbing back to check if the build passed.

![Toast notification example](Ekran%20görüntüsü%202026-07-20%20115401.png)

## What it does

Runs as a background Windows Service that polls a configured Azure DevOps pipeline for new build results. When a build completes, it sends the outcome (succeeded or failed) to a small user-side process, which pops up a native Windows toast notification telling you exactly what happened and who triggered it.

Two pieces work together:

- **`service.py`** — runs as a Windows Service (via `pywin32`), checks the pipeline on an interval, and tracks already-notified builds so you don't get duplicate alerts.
- **`user_notifier.py`** — runs in your user session, listens for messages from the service over a named pipe, and shows the toast. This split exists because Windows Services can't display UI directly in a user's desktop session.

## Features

- Automatic polling of Azure DevOps pipelines
- Native Windows toast notifications on success/failure
- Runs quietly in the background as a Windows Service
- Keeps track of already-notified builds to avoid duplicate alerts
- Simple JSON-based configuration

## How it works

1. `service.py` polls the Azure DevOps REST API for the latest pipeline run.
2. If the run is new and finished, it compares the result against `state.json` to avoid re-notifying.
3. The result is sent through a named pipe to `user_notifier.py`, which is listening in the active user session.
4. `user_notifier.py` displays a toast notification with the pipeline name, result, and who triggered it.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Configure your pipeline and Azure DevOps connection in `config.json`.
3. Set your Personal Access Token:
   ```bash
   python set_pat.py
   ```
4. Install and start the service (run as Administrator):
   ```bash
   python service.py install
   python service.py start
   ```
5. Run `user_notifier.py` in your normal user session so it can receive and display notifications.

### Running from the packaged .exe

If you don't want to run the project through Python directly, a prebuilt `main.exe` is available under the `dist` folder. From an Administrator Command Prompt:

```bash
cd dist
main.exe
```

Make sure `config.json` and `state.json` are present alongside `main.exe` in the `dist` folder before running it.

## Tech stack

- Python
- `pywin32` (Windows Service + named pipes)
- Azure DevOps REST API
- Windows Toast Notifications

## Notes

This was built as a personal productivity tool for keeping track of deployments without constantly checking Azure DevOps manually. Contributions and suggestions are welcome.
