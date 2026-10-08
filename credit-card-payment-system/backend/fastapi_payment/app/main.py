from datetime import datetime, timezone
from decimal import Decimal
import uuid

import httpx
from fastapi import FastAPI, Header, HTTPException, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from .config import (
    DJANGO_INTERNAL_URL,
    DJANGO_INTERNAL_SECRET,
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
    CORS_ALLOWED_ORIGINS,
)
from .schemas import DashboardSummary, PaymentRequest, PaymentResponse

app = FastAPI(
    title="Credit Card Payment Service",
    version="1.0.0",
    description="Simulated payment processing service. No real payment gateway is used.",
)
bearer_auth = HTTPBearer(auto_error=False)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/version")
def version():
    return {"version": "1.0.0"}

def authenticate_jwt(authorization: str | None) -> int:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer JWT token required.")
    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id") or payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid JWT payload.")
        return int(user_id)
    except (JWTError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid or expired JWT token.")

async def django_request(
    method: str,
    path: str,
    json_data: dict | None = None,
    params: dict | None = None,
):
    url = f"{DJANGO_INTERNAL_URL.rstrip('/')}{path}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.request(
            method,
            url,
            json=json_data,
            params=params,
            headers={"X-Internal-Secret": DJANGO_INTERNAL_SECRET},
        )
    if response.status_code >= 400:
        try:
            detail = response.json()
        except ValueError:
            detail = response.text
        raise HTTPException(status_code=response.status_code, detail=detail)
    return response.json()


@app.get("/dashboard/summary")
async def dashboard_summary(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_auth),
) -> DashboardSummary:
    authorization = f"Bearer {credentials.credentials}" if credentials else None
    authenticated_user_id = authenticate_jwt(authorization)
    return await django_request(
        "GET",
        "/api/internal/transactions/dashboard/summary/",
        params={"user_id": authenticated_user_id},
    )


@app.post("/payments/", response_model=PaymentResponse)
async def make_payment(
    payload: PaymentRequest,
    authorization: str | None = Header(default=None),
):
    authenticated_user_id = authenticate_jwt(authorization)
    if authenticated_user_id != payload.user_id:
        raise HTTPException(
            status_code=403,
            detail="JWT user does not match payment user.",
        )

    reference = (
        f"PAY-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-"
        f"{uuid.uuid4().hex[:8].upper()}"
    )

    # First state is always PENDING as required.
    await django_request(
        "POST",
        "/api/internal/transactions/create/",
        {
            "user_id": payload.user_id,
            "card_id": payload.card_id,
            "amount": str(payload.amount),
            "reference": reference,
        },
    )

    # Deterministic simulation: amounts ending with .13 fail.
    failed = (
        payload.amount.quantize(Decimal("0.01")) % Decimal("1")
        == Decimal("0.13")
    )
    final_status = "FAILED" if failed else "SUCCESS"
    failure_reason = "Simulated payment failure." if failed else ""

    result = await django_request(
        "PATCH",
        f"/api/internal/transactions/{reference}/",
        {"status": final_status, "failure_reason": failure_reason},
    )

    return PaymentResponse(
        reference=result["reference"],
        status=final_status,
        amount=result["amount"],
        currency=result["currency"],
        message=(
            "Payment failed (simulated)."
            if failed
            else "Payment successful (simulated)."
        ),
    )
