import subprocess
from fastapi import APIRouter
from app.models.api_schemas import HealthStatus
from app.config import settings

router = APIRouter(prefix="", tags=["System Health"])

@router.get("/health", response_model=HealthStatus)
def health_check():
    ffmpeg_exe = settings.get_ffmpeg_path()
    ffmpeg_ok = False
    ffmpeg_version = None

    try:
        res = subprocess.run([ffmpeg_exe, "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5)
        if res.returncode == 0:
            ffmpeg_ok = True
            ffmpeg_version = res.stdout.splitlines()[0] if res.stdout else "unknown"
    except Exception:
        pass

    storage_writable = False
    try:
        test_file = settings.storage_dir / ".health_test"
        test_file.write_text("ok")
        test_file.unlink()
        storage_writable = True
    except Exception:
        pass

    footage_detail = (
        "All systems operational (Real stock footage providers active)"
        if (settings.pexels_api_key or settings.pixabay_api_key)
        else "No PEXELS_API_KEY / PIXABAY_API_KEY: using procedural fallback. Set keys in .env to enable real stock footage."
    )

    return HealthStatus(
        status="healthy" if (ffmpeg_ok and storage_writable) else "degraded",
        version=settings.version,
        ffmpeg_available=ffmpeg_ok,
        ffmpeg_version=ffmpeg_version,
        storage_writable=storage_writable,
        active_jobs=0,
        details=footage_detail,
        providers_summary=settings.get_provider_status_summary()
    )

@router.get("/ready")
async def readiness_check():
    checks = {}
    failing = []

    # 1. FFmpeg
    ffmpeg_exe = settings.get_ffmpeg_path()
    try:
        res = subprocess.run([ffmpeg_exe, "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=4)
        if res.returncode == 0:
            checks["ffmpeg"] = {"ok": True, "message": "FFmpeg binary operational"}
        else:
            checks["ffmpeg"] = {"ok": False, "message": f"FFmpeg returned exit code {res.returncode}"}
            failing.append("ffmpeg")
    except Exception as e:
        checks["ffmpeg"] = {"ok": False, "message": f"FFmpeg execution failed: {str(e)[:50]}"}
        failing.append("ffmpeg")

    # 2. Storage
    try:
        settings.storage_dir.mkdir(parents=True, exist_ok=True)
        t_file = settings.storage_dir / ".ready_check"
        t_file.write_text("ok")
        t_file.unlink()
        checks["storage"] = {"ok": True, "message": "Storage directory writable"}
    except Exception as e:
        checks["storage"] = {"ok": False, "message": f"Storage not writable: {str(e)[:50]}"}
        failing.append("storage")

    # 3. Database
    try:
        import sqlite3
        db_path = settings.storage_dir / "frameflow.db"
        with sqlite3.connect(db_path) as conn:
            conn.execute("SELECT 1")
        checks["database"] = {"ok": True, "message": "Database operational"}
    except Exception as e:
        checks["database"] = {"ok": False, "message": f"Database error: {str(e)[:50]}"}
        failing.append("database")

    # 4. Enabled providers
    active_providers = []
    try:
        from app.services.footage_service import footage_service
        for p in footage_service.providers:
            if "mock" in p.name.lower():
                active_providers.append("mock_synthetic")
            elif p.is_available:
                active_providers.append(p.name.lower())
    except Exception:
        active_providers.append("mock")

    checks["providers"] = {
        "ok": len(active_providers) > 0,
        "message": f"Active footage sources: {', '.join(active_providers)}"
    }
    if not active_providers:
        failing.append("providers")

    is_ready = len(failing) == 0
    return {
        "ready": is_ready,
        "status": "ready" if is_ready else "degraded",
        "app": settings.app_name,
        "version": settings.version,
        "checks": checks,
        "failing_checks": failing
    }
