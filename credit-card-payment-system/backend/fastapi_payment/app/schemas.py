from datetime import datetime
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, Field, condecimal


class PaymentRequest(BaseModel):
    user_id: int = Field(gt=0)
    card_id: int = Field(gt=0)
    amount: condecimal(gt=Decimal("0.01"), max_digits=12, decimal_places=2)
    currency: Literal["INR"] = "INR"


class PaymentResponse(BaseModel):
    reference: str
    status: str
    amount: Decimal
    currency: str
    message: str


class TransactionSummary(BaseModel):
    model_config = {
        "json_schema_extra": {
            "examples": [{
                "id": 1,
                "amount": "125.50",
                "currency": "INR",
                "status": "SUCCESS",
                "reference": "TX-20261007-001",
                "failure_reason": "",
                "card_mask": "************4242",
                "created_at": "2026-10-07T10:00:00Z",
                "updated_at": "2026-10-07T10:00:00Z",
            }]
        }
    }

    id: int
    amount: condecimal(ge=Decimal("0.00"), max_digits=12, decimal_places=2) = Field(
        examples=["125.50"]
    )
    currency: str
    status: str
    reference: str
    failure_reason: str
    card_mask: str
    created_at: datetime
    updated_at: datetime


class DashboardSummary(BaseModel):
    model_config = {
        "json_schema_extra": {
            "examples": [{
                "total_transactions": 12,
                "total_amount_spent": "7299.00",
                "current_month_spending": "5149.00",
                "available_credit_limit": "42701.00",
                "last_5_transactions": [{
                    "id": 1,
                    "amount": "125.50",
                    "currency": "INR",
                    "status": "SUCCESS",
                    "reference": "TX-20261007-001",
                    "failure_reason": "",
                    "card_mask": "************4242",
                    "created_at": "2026-10-07T10:00:00Z",
                    "updated_at": "2026-10-07T10:00:00Z",
                }],
            }]
        }
    }

    total_transactions: int
    total_amount_spent: Decimal = Field(examples=["7299.00"])
    current_month_spending: Decimal = Field(examples=["5149.00"])
    available_credit_limit: condecimal(
        ge=Decimal("0.00"), max_digits=12, decimal_places=2
    ) = Field(examples=["42701.00"])
    last_5_transactions: list[TransactionSummary]
