from uuid import uuid4

import structlog
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.models import (
    ErrorDetail,
    ErrorResponse,
    TransactionApproved,
    TransactionRequest,
)
from app.services.validation import (
    InvalidRequestError,
    TransactionRejectedError,
    validate_transaction,
)

router = APIRouter(tags=["transactions"])


@router.post("/validate")
async def validate(request: TransactionRequest):
    trace_id = str(uuid4())

    log = structlog.get_logger().bind(
        trace_id=trace_id,
        transaction_id=str(request.transactionId),
    )
    log.info(
        "transaction.received",
        amount=request.amount,
        currency=request.currency,
        payer_id=request.payerId,
    )

    try:
        result = validate_transaction(request, trace_id)
        log.info("transaction.approved")
        return JSONResponse(
            status_code=200,
            content=result.model_dump(mode="json"),
        )

    except InvalidRequestError as e:
        log.warning("transaction.invalid", details=e.details)
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
        log.warning("transaction.rejected", details=e.details)
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
        log.error("transaction.error", error=str(e))
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
