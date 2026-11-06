# FastAPI Test App

This is a small FastAPI test app.

## Setup

Install the dependencies from the repository root:

```sh
pip install -r requirements.txt
```

Install Uvicorn separately to run the app (it is not in `requirements.txt`):

```sh
pip install uvicorn
```

## Run

```sh
uvicorn main:app --reload
```

The app runs at `http://127.0.0.1:8000`.

## Test

```sh
pytest -q
```

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
