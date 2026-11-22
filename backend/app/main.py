import sys
import time
import json
import uuid
from pathlib import Path
from contextlib import asynccontextmanager

# Ensure backend directory is in sys.path when executed directly from repository root
_backend_dir = Path(__file__).resolve().parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError

from app.config import settings
from app.core.exceptions import FrameFlowError
from app.core.logger import logger
from app.services.job_manager import job_manager
from app.api.routes_jobs import router as jobs_router
from app.api.routes_health import router as health_router
from app.api.routes_analytics import router as analytics_router
from app.api.routes_tts import router as tts_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup routine
    try:
        # 1. Log configured providers in JSON format (no secrets leaked)
        provider_summary = settings.get_provider_status_summary()
        logger.info(f"FrameFlow AI Engine Starting. Providers configured: {json.dumps(provider_summary)}")

        # 2. Detect and delete corrupt files under 1KB
        if settings.storage_dir.exists():
            for p in settings.storage_dir.rglob("*.mp4"):
                try:
                    if p.is_file() and p.stat().st_size < 1024:
                        p.unlink()
                        logger.info(f"Removed corrupt mp4 file (<1KB): {p.name}")
                except Exception:
                    pass

        # 3. Clean up orphaned running/queued jobs
        job_manager.cleanup_orphaned_jobs_on_startup()
    except Exception as e:
        logger.warning(f"Startup maintenance warning: {e}")

    yield

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="Intelligent AI Script and Voiceover to B-roll Video Engine (IncuBrix PS3)",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# CORS middleware for modern frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Correlation ID and Request Logging Middleware
@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    start_time = time.time()
    correlation_id = request.headers.get("X-Correlation-ID", f"corr_{uuid.uuid4().hex[:12]}")
    request.state.correlation_id = correlation_id

    response = await call_next(request)
    duration_ms = round((time.time() - start_time) * 1000, 2)
    response.headers["X-Correlation-ID"] = correlation_id
    response.headers["X-Response-Time-Ms"] = str(duration_ms)

    # Do not log health polling to keep logs clean
    if request.url.path not in ("/health", "/ready"):
        logger.info(
            f"{request.method} {request.url.path} - HTTP {response.status_code} ({duration_ms}ms)",
            extra={"correlation_id": correlation_id}
        )

    return response

# Custom FrameFlow Exception Handler
@app.exception_handler(FrameFlowError)
async def frameflow_error_handler(request: Request, exc: FrameFlowError):
    corr_id = getattr(request.state, "correlation_id", exc.correlation_id)
    exc.correlation_id = corr_id
    logger.error(f"Application error: {exc.code} - {exc.message}", extra={"correlation_id": corr_id})
    return exc.to_response()

# FastAPI Validation Error Handler (Standardized Structured JSON format)
@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    corr_id = getattr(request.state, "correlation_id", None)
    err_body = {
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Request payload validation failed",
            "details": exc.errors(),
            "correlation_id": corr_id
        }
    }
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=err_body)

# Generic Unhandled Exception Handler
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    corr_id = getattr(request.state, "correlation_id", None)
    logger.error(f"Unhandled server error: {exc}", exc_info=True, extra={"correlation_id": corr_id})
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An internal server error occurred",
                "retryable": True,
                "correlation_id": corr_id
            }
        }
    )

# Static file serving for generated video artifacts
settings.storage_dir.mkdir(parents=True, exist_ok=True)
app.mount("/storage", StaticFiles(directory=str(settings.storage_dir)), name="storage")

# Include Routers
app.include_router(health_router)
app.include_router(jobs_router, prefix=settings.api_prefix)
app.include_router(analytics_router, prefix=settings.api_prefix)
app.include_router(tts_router, prefix=settings.api_prefix)

# Mount Frontend static SPA build if present
frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True, app_dir=str(_backend_dir))
