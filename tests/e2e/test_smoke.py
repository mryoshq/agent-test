"""Smoke test over real HTTP. check.sh starts uvicorn and sets E2E_BASE_URL."""

import os
from datetime import datetime

import httpx
import pytest

pytestmark = pytest.mark.e2e


@pytest.fixture
def http() -> httpx.Client:
    return httpx.Client(base_url=os.environ["E2E_BASE_URL"], timeout=10)


def test_health_over_http(http: httpx.Client) -> None:
    response = http.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_version_over_http(http: httpx.Client) -> None:
    response = http.get("/version")
    assert response.status_code == 200
    assert response.json() == {"version": "0.1.0"}


def test_time_over_http(http: httpx.Client) -> None:
    response = http.get("/time")
    assert response.status_code == 200
    assert datetime.fromisoformat(response.json()["time"]).utcoffset() is not None
