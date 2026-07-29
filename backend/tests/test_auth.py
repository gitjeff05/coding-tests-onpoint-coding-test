import base64

from fastapi.testclient import TestClient

from app.auth import AUTH_PASSWORD, AUTH_USERNAME
from app.main import app


def test_missing_credentials_rejected():
    res = TestClient(app).get("/api/tree")
    assert res.status_code == 401


def test_wrong_basic_credentials_rejected():
    bad = base64.b64encode(b"wrong:wrong").decode()
    res = TestClient(app, headers={"Authorization": f"Basic {bad}"}).get("/api/tree")
    assert res.status_code == 401


def test_garbage_authorization_header_rejected():
    res = TestClient(app, headers={"Authorization": "gibberish"}).get("/api/tree")
    assert res.status_code == 401


def test_correct_basic_credentials_accepted(client):
    res = client.get("/api/tree")
    assert res.status_code == 200


def test_login_rejects_bad_credentials():
    res = TestClient(app).post("/auth/login", json={"username": "nope", "password": "nope"})
    assert res.status_code == 401


def test_login_issues_jwt_usable_as_bearer_token():
    res = TestClient(app).post(
        "/auth/login", json={"username": AUTH_USERNAME, "password": AUTH_PASSWORD}
    )
    assert res.status_code == 200
    body = res.json()
    assert body["token_type"] == "bearer"
    token = body["access_token"]

    authed = TestClient(app, headers={"Authorization": f"Bearer {token}"}).get("/api/tree")
    assert authed.status_code == 200
