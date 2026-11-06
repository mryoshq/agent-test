# FastAPI Test App

This is a small FastAPI test app.

## Setup

Install the runtime and development dependencies (versions are pinned):

```sh
pip install -r requirements-dev.txt
```

## Run

```sh
uvicorn main:app --reload
```

The app runs at `http://127.0.0.1:8000`.

## Checks

The same commands CI runs (lint, types, unit tests with the coverage floor, security, e2e):

```sh
bash .github/scripts/check.sh all
```

Project rules for agents and humans are in [AGENTS.md](AGENTS.md).

## Endpoints

- **`GET /health`** — Returns the app's health status.

  Example response:

  ```json
  {"status": "ok"}
  ```

- **`GET /version`** — Returns the app version.

  Example response:

  ```json
  {"version": "0.1.0"}
  ```

- **`GET /time`** — Returns the current UTC time in ISO 8601 format. The value changes with each request.

  Example response:

  ```json
  {"time": "2026-11-06T12:34:56.123456+00:00"}
  ```
