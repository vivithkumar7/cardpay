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
