import time
import uvicorn

from src.utils.logger import logger as log, setup_json_logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from http.client import responses
from src.telemetry import get_trace_context, setup_telemetry
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from src.settings import get_settings

from src.controllers.api import routers
from src.utils.general import timestamp

setup_json_logging(service=get_settings().service_name, environment=get_settings().env)


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    """Manage application lifecycle: startup and shutdown events."""
    # TODO
    log.info("Application startup complete")
    yield
    log.info("Application shutdown complete")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Emit one structured JSON log line per HTTP request.

    Fields: endpoint, method, status_code, duration_ms, trace_id, span_id.
    trace_id and span_id are populated from the active OpenTelemetry span so
    that log lines can be correlated with distributed traces — equivalent to
    BmLogger's behaviour in the NestJS services.
    """

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        status_code = 500
        trace_ctx = get_trace_context()
        with log.contextualize(
            endpoint=request.url.path,
            method=request.method,
            trace_id=trace_ctx["trace_id"],
            span_id=trace_ctx["span_id"],
        ):
            try:
                response = await call_next(request)
                status_code = response.status_code
                return response
            finally:
                duration_ms = round((time.perf_counter() - start) * 1000, 2)
                log.bind(status_code=status_code, duration_ms=duration_ms).info("HTTP request")


app = FastAPI(
    title=get_settings().service_name,
    version="0.1.0",
    description="Capple Fastapi backend",
    # TODO: servers
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_version=get_settings().openapi_version,
    lifespan=app_lifespan,
)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request,
    exc: HTTPException,
) -> JSONResponse:
    return JSONResponse(
        content={"errorMessage": exc.detail, "errorCode": responses[exc.status_code], "timestamp": timestamp()},
        status_code=exc.status_code,
    )


def _sanitize_errors(errors: list[dict]) -> list[dict]:
    """Make Pydantic error dicts JSON-serialisable by converting non-primitive
    values (e.g. nested Exception objects in ``ctx``) to strings."""

    def _sanitize(obj):
        if isinstance(obj, dict):
            return {k: _sanitize(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [_sanitize(i) for i in obj]
        if isinstance(obj, Exception):
            return str(obj)
        return obj

    return [_sanitize(err) for err in errors]


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    return JSONResponse(
        content={
            "errorMessage": "Invalid request, check your input parameters",
            "errorCode": responses[status.HTTP_422_UNPROCESSABLE_ENTITY],
            "timestamp": timestamp(),
            "errorDetails": _sanitize_errors(exc.errors()),
        },
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )


setup_telemetry(
    app,
    ignore_paths=["/api/healthcheck", "/api/readiness"],
)

for router in routers:
    app.include_router(router)

app.add_middleware(RequestLoggingMiddleware)

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(app, host=settings.host, port=settings.port)
