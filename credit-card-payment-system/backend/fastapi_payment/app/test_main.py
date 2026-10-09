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

def test_api_request_logs_status_and_response_time(caplog):
    with caplog.at_level("INFO", logger="api.monitoring"):
        response = client.get("/health")
    assert response.status_code == 200
    assert "path=/health" in caplog.text
    assert "status=200" in caplog.text
    assert "duration_ms=" in caplog.text

def test_api_failure_is_logged_as_warning(caplog):
    with caplog.at_level("WARNING", logger="api.monitoring"):
        response = client.get("/missing-route")
    assert response.status_code == 404
    assert "path=/missing-route" in caplog.text
    assert "status=404" in caplog.text

def test_version():
    response = client.get("/version")
    assert response.status_code == 200
    assert "version" in response.json()

def test_payment_cors_preflight():
    response = client.options("/payments/", headers={
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "authorization,content-type,x-device-id",
    })
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "authorization" in response.headers["access-control-allow-headers"].lower()
    assert "x-device-id" in response.headers["access-control-allow-headers"].lower()

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


def test_dashboard_summary_openapi_documents_bearer_auth_and_response_fields():
    operation = app.openapi()["paths"]["/dashboard/summary"]["get"]
    assert {"HTTPBearer": []} in operation["security"]
    response_schema = operation["responses"]["200"]["content"]["application/json"]["schema"]
    assert response_schema["$ref"] == "#/components/schemas/DashboardSummary"
    summary_fields = app.openapi()["components"]["schemas"]["DashboardSummary"]["properties"]
    assert set(summary_fields) == {
        "total_transactions",
        "total_amount_spent",
        "current_month_spending",
        "available_credit_limit",
        "last_5_transactions",
    }
    transaction_fields = app.openapi()["components"]["schemas"]["TransactionSummary"]["properties"]
    assert {
        "amount",
        "card_mask",
        "created_at",
        "fraud_status",
        "status",
    } <= set(transaction_fields)


def test_dashboard_summary_forwards_authenticated_user_to_django():
    summary = {
        "total_transactions": 2,
        "total_amount_spent": "20.00",
        "current_month_spending": "10.00",
        "available_credit_limit": "80.00",
        "last_5_transactions": [{
            "id": 1,
            "amount": "10.00",
            "currency": "INR",
            "status": "SUCCESS",
            "fraud_status": "CLEAR",
            "reference": "TX-SUMMARY-1",
            "failure_reason": "",
            "card_mask": "************1111",
            "created_at": "2026-10-07T10:00:00Z",
            "updated_at": "2026-10-07T10:00:00Z",
        }],
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
        {"reference":"PAY-1","status":"PENDING","amount":"100.00","currency":"INR","fraud_status":"CLEAR"},
        {"reference":"PAY-1","status":"SUCCESS","amount":"100.00","currency":"INR","fraud_status":"FLAGGED"}
    ])) as django_request:
        response = client.post("/payments/", json={
            "user_id": 1, "card_id": 1, "amount": "100.00",
            "category": "FOOD", "currency": "INR"
        }, headers={**auth_headers(), "X-Device-ID": "browser-device-1"})
    assert response.status_code == 200
    assert response.json()["status"] == "SUCCESS"
    assert response.json()["fraud_status"] == "FLAGGED"
    create_payload = django_request.await_args_list[0].args[2]
    assert create_payload["category"] == "FOOD"
    assert create_payload["source_ip"] == "testclient"
    assert create_payload["device_id"] == "browser-device-1"

def test_payment_defaults_category_to_other():
    with patch("app.main.django_request", new=AsyncMock(side_effect=[
        {"reference":"PAY-3","status":"PENDING","amount":"100.00","currency":"INR","fraud_status":"CLEAR"},
        {"reference":"PAY-3","status":"SUCCESS","amount":"100.00","currency":"INR","fraud_status":"CLEAR"}
    ])) as django_request:
        response = client.post("/payments/", json={
            "user_id": 1, "card_id": 1, "amount": "100.00"
        }, headers=auth_headers())
    assert response.status_code == 200
    assert django_request.await_args_list[0].args[2]["category"] == "OTHER"

def test_payment_rejects_unsupported_category():
    with patch("app.main.django_request", new=AsyncMock()) as django_request:
        response = client.post("/payments/", json={
            "user_id": 1, "card_id": 1, "amount": "100.00", "category": "GAMBLING"
        }, headers=auth_headers())
    assert response.status_code == 422
    django_request.assert_not_awaited()

def test_payment_failure():
    with patch("app.main.django_request", new=AsyncMock(side_effect=[
        {"reference":"PAY-2","status":"PENDING","amount":"100.13","currency":"INR","fraud_status":"CLEAR"},
        {"reference":"PAY-2","status":"FAILED","amount":"100.13","currency":"INR","fraud_status":"CLEAR"}
    ])):
        response = client.post("/payments/", json={
            "user_id": 1, "card_id": 1, "amount": "100.13", "currency": "INR"
        }, headers=auth_headers())
    assert response.status_code == 200
    assert response.json()["status"] == "FAILED"
