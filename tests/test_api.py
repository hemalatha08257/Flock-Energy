from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_login_and_meter_list():
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "operator@urja.local", "password": "urja-ops-2026"},
    )
    assert login_response.status_code == 200
    payload = login_response.json()
    assert payload["authenticated"] is True

    meters_response = client.get("/api/v1/meters")
    assert meters_response.status_code == 200
    data = meters_response.json()
    assert isinstance(data, dict)
    assert "meters" in data
    assert isinstance(data["meters"], list)


def test_dashboard_home_logout_and_history_endpoints():
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "operator@urja.local", "password": "urja-ops-2026"},
    )
    assert login_response.status_code == 200

    dashboard_response = client.get("/api/v1/dashboard")
    assert dashboard_response.status_code == 200
    dashboard = dashboard_response.json()
    assert "totals" in dashboard or "summary" in dashboard

    home_response = client.get("/api/v1/home")
    assert home_response.status_code == 200
    assert home_response.json()["service"] == "Urja Meter Ops"

    logout_response = client.post("/api/v1/auth/logout")
    assert logout_response.status_code == 200
    assert logout_response.json()["logged_out"] is True

    history_response = client.get("/api/v1/history")
    assert history_response.status_code == 200
    history = history_response.json()
    assert "events" in history
    assert isinstance(history["events"], list)
