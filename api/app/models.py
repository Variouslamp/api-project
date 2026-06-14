from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime


class TransactionRequest(BaseModel):
    transactionId: UUID
    amount: float = Field(ge=1)
    currency: str
    payerId: str
    timestamp: datetime


class TransactionApproved(BaseModel):
    status: str = "APROVED"
    message: str = "La transaccion fue procesada correctamente"
    processedAt: datetime
    traceId: str


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: list[str]
    traceId: str


class ErrorResponse(BaseModel):
    error: ErrorDetail
