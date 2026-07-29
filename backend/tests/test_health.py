from fastapi.testclient import TestClient

from app.main import app


def test_health_ok_without_auth():
    res = TestClient(app).get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok", "db": True}


def test_metrics_exposed_without_auth():
    res = TestClient(app).get("/metrics")
    assert res.status_code == 200
