def test_register_success(client, user_payload):
    resp = client.post("/api/v1/auth/register", json=user_payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["token_type"] == "bearer"
    assert data["access_token"]
    assert data["user"]["username"] == "tester"
    assert "password" not in data["user"]


def test_register_duplicate_email(client, user_payload):
    client.post("/api/v1/auth/register", json=user_payload)
    resp = client.post("/api/v1/auth/register", json=user_payload)
    assert resp.status_code == 409


def test_login_success(client, user_payload):
    client.post("/api/v1/auth/register", json=user_payload)
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": user_payload["email"], "password": user_payload["password"]},
    )
    assert resp.status_code == 200
    assert resp.json()["access_token"]


def test_login_wrong_password(client, user_payload):
    client.post("/api/v1/auth/register", json=user_payload)
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": user_payload["email"], "password": "wrong-password"},
    )
    assert resp.status_code == 401


def test_refresh_token(client, user_payload):
    resp = client.post("/api/v1/auth/register", json=user_payload)
    refresh = resp.json()["refresh_token"]
    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert resp.status_code == 200
    assert resp.json()["access_token"]
