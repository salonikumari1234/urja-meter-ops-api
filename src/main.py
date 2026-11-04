from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from src.api.middleware.request_id import RequestIDAndLoggingMiddleware
from src.api.routes import api_router
from src.clients.portal_client import UrjaPortalClient
from src.config.settings import settings
from src.core.exceptions import AppException
from src.core.logging import logger
from src.repositories.cache_repository import cache_repository
from src.schemas.common import ErrorDetail, ErrorEnvelope


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manages application lifecycle: startup warming and graceful shutdown."""
    logger.info(f"Starting {settings.project_name} v{settings.version} [{settings.environment}]")
    client = UrjaPortalClient()

    # In production/development, pre-warm cache; skip in test environments
    if settings.environment.lower() not in ("test", "testing"):
        try:
            logger.info("Pre-warming repository cache from upstream Urja portal...")
            await cache_repository.ensure_synced(client)
        except Exception as exc:
            logger.warning(
                f"Pre-warm sync encountered non-fatal error during startup: {exc}. "
                "Cache will synchronize on first incoming request."
            )

    yield

    logger.info("Shutting down application and closing upstream connections...")
    await client.close()


app = FastAPI(
    title=settings.project_name,
    version=settings.version,
    description=(
        "Production-grade RESTful API service exposing and normalizing data "
        "from the upstream Urja Meter Ops portal."
    ),
    openapi_url=f"{settings.api_v1_str}/openapi.json",
    docs_url=f"{settings.api_v1_str}/docs",
    redoc_url=f"{settings.api_v1_str}/redoc",
    lifespan=lifespan
)

# 1. CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"]
)

# 2. Request ID & Structured Logging Middleware
app.add_middleware(RequestIDAndLoggingMiddleware)

# 3. Centralized Exception Handlers
@app.exception_handler(AppException)
async def handle_app_exception(request: Request, exc: AppException) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    error_payload = ErrorEnvelope(
        success=False,
        error=ErrorDetail(
            code=exc.code,
            message=exc.message,
            details=exc.details
        ),
        request_id=request_id
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload.model_dump()
    )


@app.exception_handler(RequestValidationError)
async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    errors = []
    for err in exc.errors():
        loc = " -> ".join(str(p) for p in err.get("loc", []))
        errors.append(f"{loc}: {err.get('msg')}")

    error_payload = ErrorEnvelope(
        success=False,
        error=ErrorDetail(
            code="INVALID_PARAMETER",
            message="Request parameter validation failed.",
            details=errors
        ),
        request_id=request_id
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_payload.model_dump()
    )


@app.exception_handler(Exception)
async def handle_unexpected_exception(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    error_payload = ErrorEnvelope(
        success=False,
        error=ErrorDetail(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected server error occurred. Please contact the administrator."
        ),
        request_id=request_id
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_payload.model_dump()
    )


# 4. Mount API v1 Routes
app.include_router(api_router, prefix=settings.api_v1_str)
