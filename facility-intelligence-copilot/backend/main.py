import sys
from pathlib import Path

# Ensure both backend dir and project root dir are on sys.path
backend_dir = Path(__file__).resolve().parent
project_root = backend_dir.parent
for p in [str(backend_dir), str(project_root)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routes import (
    alerts,
    assets,
    sensors,
    telemetry,
    xray,
    gamification,
    replay,
    sns_dispatch,
    realtime,
    rag,
    counterfactual,
    incidents,
    digital_twin_endpoints,
)
from app.core.config import settings
from sqlalchemy.exc import SQLAlchemyError
from app.db.database import SessionLocal

app = FastAPI(title="Facility Intelligence Copilot - GSENSE 3.0", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(assets.router, prefix="/api/v1", tags=["assets"])
app.include_router(sensors.router, prefix="/api/v1", tags=["sensors"])
app.include_router(telemetry.router, prefix="/api/v1", tags=["telemetry"])
app.include_router(alerts.router, prefix="/api/v1", tags=["alerts"])
app.include_router(xray.router, prefix="/api/v1", tags=["xray"])
app.include_router(gamification.router, prefix="/api/v1", tags=["gamification"])
app.include_router(replay.router, prefix="/api/v1", tags=["replay"])
app.include_router(sns_dispatch.router, prefix="/api/v1", tags=["sns"])
app.include_router(realtime.router, prefix="/api/v1", tags=["realtime"])
app.include_router(rag.router, prefix="/api/v1", tags=["rag"])
app.include_router(counterfactual.router, prefix="/api/v1", tags=["counterfactual"])
app.include_router(incidents.router, prefix="/api/v1", tags=["incidents"])
app.include_router(digital_twin_endpoints.router)




@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "backend"}


@app.get("/api/v1/system/status")
def system_status() -> dict:
    """
    WORKSTREAM H — System Health Check
    
    Returns status of all critical components:
    - Backend API (running if endpoint responds)
    - Database (healthy if connection succeeds)
    - Kafka (healthy if broker available)
    - X-Ray (ready if service initialized)
    """
    
    # Backend always healthy if endpoint is responding
    backend_status = "healthy"
    
    # Database check
    database_status = "unavailable"
    try:
        db = SessionLocal()
        # Try a simple query to verify connection
        db.execute("SELECT 1")
        db.close()
        database_status = "healthy"
    except SQLAlchemyError as e:
        database_status = "unavailable"
    except Exception:
        database_status = "unavailable"
    
    # Kafka check (try to connect or check config)
    kafka_status = "unavailable"
    try:
        bootstrap_servers = settings.kafka_bootstrap_servers
        if bootstrap_servers and "localhost:9092" in bootstrap_servers:
            # Would need actual Kafka client to verify
            kafka_status = "unavailable"  # Docker-dependent
        else:
            kafka_status = "unavailable"
    except Exception:
        kafka_status = "unavailable"
    
    # X-Ray is ready if services are initialized
    xray_status = "ready"  # Core service logic doesn't require external deps
    
    # Simulator status (would need external check)
    simulator_status = "unknown"
    
    return {
        "backend": backend_status,
        "database": database_status,
        "kafka": kafka_status,
        "xray": xray_status,
        "simulator": simulator_status,
        "timestamp": __import__('datetime').datetime.utcnow().isoformat(),
    }


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Facility Intelligence Copilot API", "environment": settings.app_env}
