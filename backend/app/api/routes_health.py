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

    return HealthStatus(
        status="healthy" if (ffmpeg_ok and storage_writable) else "degraded",
        version=settings.version,
        ffmpeg_available=ffmpeg_ok,
        ffmpeg_version=ffmpeg_version,
        storage_writable=storage_writable,
        active_jobs=0
    )

@router.get("/ready")
def readiness_check():
    return {"ready": True, "app": settings.app_name, "version": settings.version}
