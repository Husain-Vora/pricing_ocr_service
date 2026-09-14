import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.api import ocr, pricing, receipt
from app.core.config import get_settings
from app.core.errors import AppError
from app.core.logging import configure_logging, get_logger
from app.core.request_context import get_request_id, new_request_id, set_request_id

settings = get_settings()
configure_logging(level=settings.LOG_LEVEL)
logger = get_logger(__name__)

app = FastAPI(
    title="Pricing Anomaly, OCR & Receipt Item Analysis Service",
    description=(
        "Independent Python service for price anomaly scoring, OCR extraction "
        "and combined receipt-item scoring. Called by a .NET application over "
        "HTTP; does not own the .NET workflow, approval or expense database."
    ),
    version="0.1.0",
)


@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    incoming = request.headers.get("x-request-id")
    request_id = incoming or new_request_id()
    set_request_id(request_id)
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    logger.warning("AppError: code=%s message=%s", exc.code, exc.message)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "request_id": get_request_id() or "-",
                "details": exc.details,
            }
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # Never leak stack traces or internals to the caller.
    logger.exception("Unhandled exception")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred.",
                "request_id": get_request_id() or "-",
                "details": {},
            }
        },
    )


# Application-facing business endpoints (frozen, Phase 0):
app.include_router(pricing.router)
app.include_router(ocr.router)
app.include_router(receipt.router)


@app.get("/healthz", tags=["operational"])
def healthz() -> dict:
    """Operational health check. Not one of the three business endpoints."""
    return {"status": "ok", "env": settings.APP_ENV}


@app.get("/readyz", tags=["operational"])
def readyz() -> dict:
    """Operational readiness check. Becomes model-aware from Phase 4 onward."""
    return {"status": "ready", "model_version": settings.MODEL_VERSION}
