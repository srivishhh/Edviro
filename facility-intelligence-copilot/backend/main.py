import logging
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.api.v1.routes import alerts, assets, incident_graph, integrations, sensors, telemetry, whatif, xray
from app.core.config import settings
from app.core.middleware import CorrelationIdMiddleware, SecurityHeadersMiddleware
from app.db.database import SessionLocal

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Facility Intelligence Copilot",
    version="0.1.0",
    docs_url="/docs" if settings.app_env != "production" else None,
    redoc_url="/redoc" if settings.app_env != "production" else None,
)

# 1. Register Middlewares
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(CorrelationIdMiddleware)

# 2. CORS Hardening
raw_origins = settings.cors_allowed_origins or "http://localhost:5173,http://127.0.0.1:5173"
allowed_origins = [orig.strip() for orig in raw_origins.split(",") if orig.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key", "X-Request-ID", "X-SNS-Signature", "Accept"],
)

# 3. Safe Global Exception Handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    logger.warning("HTTPException [%s]: %s (request_id=%s)", exc.status_code, exc.detail, request_id)
    return JSONResponse(
        status_code=exc.status_code,
        headers=exc.headers,
        content={
            "error": {
                "code": "HTTP_ERROR",
                "message": exc.detail,
                "request_id": request_id,
            }
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    logger.warning("RequestValidationError: %s (request_id=%s)", exc.errors(), request_id)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request payload format or value.",
                "details": exc.errors(),
                "request_id": request_id,
            }
        },
    )


@app.exception_handler(Exception)
async def global_unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error("Unhandled server error: %s (request_id=%s)", exc, request_id, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected server error occurred. Please contact system administrator.",
                "request_id": request_id,
            }
        },
    )


# 4. Register Routers
app.include_router(assets.router, prefix="/api/v1", tags=["assets"])
app.include_router(sensors.router, prefix="/api/v1", tags=["sensors"])
app.include_router(telemetry.router, prefix="/api/v1", tags=["telemetry"])
app.include_router(alerts.router, prefix="/api/v1", tags=["alerts"])
app.include_router(xray.router, prefix="/api/v1", tags=["xray"])
app.include_router(integrations.router, prefix="/api/v1", tags=["integrations"])
app.include_router(whatif.router, prefix="/api/v1", tags=["whatif"])
app.include_router(whatif.router, prefix="/api", tags=["whatif"])
app.include_router(incident_graph.router, prefix="/api/v1", tags=["incident-graph"])
app.include_router(incident_graph.router, prefix="/api", tags=["incident-graph"])


# 5. Public Health & System Status Endpoints
@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "backend"}


@app.get("/api/v1/system/status")
def system_status() -> dict:
    """
    Returns high-level status of critical components without leaking internal credentials or stack traces.
    """
    backend_status = "healthy"

    database_status = "unavailable"
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        database_status = "healthy"
    except (SQLAlchemyError, Exception):
        database_status = "unavailable"

    kafka_status = "unavailable"
    try:
        bootstrap_servers = settings.kafka_bootstrap_servers
        if bootstrap_servers and "localhost:9092" in bootstrap_servers:
            kafka_status = "unavailable"
        else:
            kafka_status = "unavailable"
    except Exception:
        kafka_status = "unavailable"

    xray_status = "ready"
    simulator_status = "unknown"

    return {
        "backend": backend_status,
        "database": database_status,
        "kafka": kafka_status,
        "xray": xray_status,
        "simulator": simulator_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Facility Intelligence Copilot API", "environment": settings.app_env}

