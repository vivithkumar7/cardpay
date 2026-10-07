from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from jose import jwt
from app.main import app
from app.config import JWT_ALGORITHM, JWT_SECRET_KEY

client = TestClient(app)

def auth_headers(user_id=1):
    token = jwt.encode({"user_id": user_id}, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return {"Authorization": f"Bearer {token}"}

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_version():
    response = client.get("/version")
    assert response.status_code == 200
    assert "version" in response.json()

def test_payment_cors_preflight():
    response = client.options("/payments/", headers={
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "authorization,content-type",
    })
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "authorization" in response.headers["access-control-allow-headers"].lower()

def test_payment_requires_jwt():
    with patch("app.main.django_request", new=AsyncMock()) as django_request:
        response = client.post("/payments/", json={
            "user_id": 1, "card_id": 1, "amount": "100.00", "currency": "INR"
        })
    assert response.status_code == 401
    django_request.assert_not_awaited()


def test_dashboard_summary_requires_jwt():
    with patch("app.main.django_request", new=AsyncMock()) as django_request:
        response = client.get("/dashboard/summary")
    assert response.status_code == 401
    django_request.assert_not_awaited()


def test_dashboard_summary_forwards_authenticated_user_to_django():
    summary = {
        "total_transactions": 2,
        "total_amount_spent": "20.00",
        "current_month_spending": "10.00",
        "available_credit_limit": "80.00",
        "last_5_transactions": [],
    }
    with patch(
        "app.main.django_request",
        new=AsyncMock(return_value=summary),
    ) as django_request:
        response = client.get("/dashboard/summary", headers=auth_headers(user_id=7))

    assert response.status_code == 200
    assert response.json() == summary
    django_request.assert_awaited_once_with(
        "GET",
        "/api/internal/transactions/dashboard/summary/",
        params={"user_id": 7},
    )


def test_payment_user_must_match_jwt():
    with patch("app.main.django_request", new=AsyncMock()) as django_request:
        response = client.post(
            "/payments/",
            json={"user_id": 1, "card_id": 1, "amount": "100.00", "currency": "INR"},
            headers=auth_headers(user_id=2),
        )
    assert response.status_code == 403
    django_request.assert_not_awaited()

def test_payment_rejects_unsupported_currency():
    with patch("app.main.django_request", new=AsyncMock()) as django_request:
        response = client.post(
            "/payments/",
            json={"user_id": 1, "card_id": 1, "amount": "100.00", "currency": "USD"},
            headers=auth_headers(),
        )
    assert response.status_code == 422
    django_request.assert_not_awaited()

def test_payment_success():
    with patch("app.main.django_request", new=AsyncMock(side_effect=[
        {"reference":"PAY-1","status":"PENDING","amount":"100.00","currency":"INR"},
        {"reference":"PAY-1","status":"SUCCESS","amount":"100.00","currency":"INR"}
    ])):
        response = client.post("/payments/", json={
            "user_id": 1, "card_id": 1, "amount": "100.00", "currency": "INR"
        }, headers=auth_headers())
    assert response.status_code == 200
    assert response.json()["status"] == "SUCCESS"

def test_payment_failure():
    with patch("app.main.django_request", new=AsyncMock(side_effect=[
        {"reference":"PAY-2","status":"PENDING","amount":"100.13","currency":"INR"},
        {"reference":"PAY-2","status":"FAILED","amount":"100.13","currency":"INR"}
    ])):
        response = client.post("/payments/", json={
            "user_id": 1, "card_id": 1, "amount": "100.13", "currency": "INR"
        }, headers=auth_headers())
    assert response.status_code == 200
    assert response.json()["status"] == "FAILED"
