from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.logging_config import configure_logging
from app.models import ErrorDetail, ErrorResponse
from app.routers.transactions import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    yield


app = FastAPI(
    title="Servicio de Validación de Transacciones",
    lifespan=lifespan,
)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    request: Request, exc: RequestValidationError
):
    trace_id = str(uuid4())
    details: list[str] = []
    for err in exc.errors():
        field = " -> ".join(str(loc) for loc in err.get("loc", []))
        msg = err.get("msg", "")
        details.append(f"{field}: {msg}")

    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            error=ErrorDetail(
                code="INVALID_REQUEST",
                message="Los datos enviados no cumplen con el formato requerido",
                details=details,
                traceId=trace_id,
            )
            ).model_dump(mode="json"),
    )


app.include_router(router, prefix="/transactions")
