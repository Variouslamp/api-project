import logging
from uuid import uuid4

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.models import ErrorDetail, ErrorResponse, TransactionRequest
from app.services.validation import (
    InvalidRequestError,
    TransactionRejectedError,
    validate_transaction,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["transactions"])


@router.post("/validate")
async def validate(request: TransactionRequest):
    trace_id = str(uuid4())

    req_data = {
        "transactionId": str(request.transactionId),
        "amount": request.amount,
        "currency": request.currency,
        "payerId": request.payerId,
    }
    resp_status = None
    resp_data: dict = {}

    try:
        result = validate_transaction(request, trace_id)
        resp_status = 200
        resp_data = {"event": "transaction.approved"}
        return JSONResponse(
            status_code=200,
            content=result.model_dump(mode="json"),
        )

    except InvalidRequestError as e:
        resp_status = 400
        resp_data = {
            "event": "transaction.invalid",
            "details": "; ".join(e.details),
        }
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                error=ErrorDetail(
                    code="INVALID_REQUEST",
                    message="Los datos enviados no cumplen con el formato requerido",
                    details=e.details,
                    traceId=trace_id,
                )
            ).model_dump(mode="json"),
        )

    except TransactionRejectedError as e:
        resp_status = 409
        resp_data = {
            "event": "transaction.rejected",
            "details": "; ".join(e.details),
        }
        return JSONResponse(
            status_code=409,
            content=ErrorResponse(
                error=ErrorDetail(
                    code="TRANSACTION_REJECTED",
                    message="La transaccion no pudo completarse",
                    details=e.details,
                    traceId=trace_id,
                )
            ).model_dump(mode="json"),
        )

    except Exception as e:
        resp_status = 500
        resp_data = {
            "event": "transaction.error",
            "details": str(e),
        }
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error=ErrorDetail(
                    code="INTERNAL_ERROR",
                    message="Ocurrio un error inesperado al procesar la solicitud",
                    details=[],
                    traceId=trace_id,
                )
            ).model_dump(mode="json"),
        )

    finally:
        logger.info(
            "",
            extra={
                "trace_id": trace_id,
                "request_data": req_data,
                "response_status": resp_status,
                "response_data": resp_data,
            },
        )
