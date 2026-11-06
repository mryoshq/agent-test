from datetime import datetime, timezone

from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/version")
def version():
    return {"version": "0.1.0"}


@app.get("/time")
def time():
    return {"time": datetime.now(timezone.utc).isoformat()}
