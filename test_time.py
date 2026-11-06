from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_time():
    requested_at = datetime.now(timezone.utc)
    response = client.get("/time")
    received_at = datetime.now(timezone.utc)

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"time"}
    assert isinstance(payload["time"], str)
    current_time = datetime.fromisoformat(payload["time"])
    assert current_time.tzinfo is not None
    assert current_time.utcoffset() == timedelta(0)
    assert requested_at <= current_time <= received_at
    assert abs(current_time - requested_at) < timedelta(seconds=5)
