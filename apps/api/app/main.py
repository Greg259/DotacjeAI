import logging
import time
import uuid
from collections import defaultdict, deque

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.admin import router as admin_router
from app.api.health import router as health_router
from app.api.programs import router as programs_router
from app.core.config import get_settings
from app.core.logging import configure_logging

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger("dotacje_ai.api")
request_windows: dict[str, deque[float]] = defaultdict(deque)

app = FastAPI(title="DotacjeAI API", version=settings.app_version)
app.include_router(health_router, prefix="/api")
app.include_router(programs_router, prefix="/api")
app.include_router(admin_router)


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    forwarded = request.headers.get("x-forwarded-for", "")
    client_ip = forwarded.split(",", 1)[0].strip() or (
        request.client.host if request.client else "unknown"
    )
    now = time.monotonic()
    window = request_windows[client_ip]
    while window and now - window[0] > 60:
        window.popleft()
    limit = 60 if request.url.path.startswith("/admin") else 180
    if len(window) >= limit:
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests"},
            headers={"Retry-After": "60"},
        )
    window.append(now)
    return await call_next(request)


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
