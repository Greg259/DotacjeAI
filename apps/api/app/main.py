import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.health import router as health_router
from app.api.programs import router as programs_router
from app.core.config import get_settings
from app.core.logging import configure_logging

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger("dotacje_ai.api")

app = FastAPI(title="DotacjeAI API", version=settings.app_version)
app.include_router(health_router, prefix="/api")
app.include_router(programs_router, prefix="/api")


@app.middleware("http")
async def request_logging(request: Request, call_next):
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    started = time.perf_counter()
    response = await call_next(request)
    response.headers["x-request-id"] = request_id
    logger.info(
        "request_completed method=%s path=%s status=%s duration_ms=%s request_id=%s",
        request.method,
        request.url.path,
        response.status_code,
        round((time.perf_counter() - started) * 1000, 2),
        request_id,
    )
    return response


@app.exception_handler(Exception)
async def unhandled_exception(request: Request, exception: Exception) -> JSONResponse:
    logger.exception("unhandled_exception path=%s", request.url.path, exc_info=exception)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
