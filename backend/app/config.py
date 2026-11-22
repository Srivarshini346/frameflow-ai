import os
import sys
from pathlib import Path
from pydantic import BaseModel, Field

# Determine base paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
STORAGE_DIR = Path(os.getenv("STORAGE_DIR", str(BASE_DIR / "storage")))
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

class Settings(BaseModel):
    app_name: str = "FrameFlow AI – Intelligent B-roll Studio"
    version: str = "1.0.0"
    api_prefix: str = "/api/v1"
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    debug: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")
    
    # Storage settings
    storage_dir: Path = STORAGE_DIR
    base_url: str = os.getenv("BASE_URL", "http://localhost:8000")
    
    # FFmpeg executable (auto-detects imageio-ffmpeg if not in system PATH)
    ffmpeg_binary: str = os.getenv("FFMPEG_BINARY", "")
    
    # Footage Provider API keys (Optional; mock provider is active when empty)
    pexels_api_key: str = os.getenv("PEXELS_API_KEY", "")
    pixabay_api_key: str = os.getenv("PIXABAY_API_KEY", "")
    enable_mock_footage: bool = os.getenv("ENABLE_MOCK_FOOTAGE", "true").lower() in ("true", "1", "yes")
    
    # Webhook signature secret
    webhook_secret: str = os.getenv("WEBHOOK_SECRET", "frameflow_default_secret_key_2026")
    
    # Concurrency and Job limits
    max_concurrent_jobs: int = int(os.getenv("MAX_CONCURRENT_JOBS", "4"))
    job_retries: int = int(os.getenv("JOB_RETRIES", "2"))
    
    def get_ffmpeg_path(self) -> str:
        if self.ffmpeg_binary and os.path.exists(self.ffmpeg_binary):
            return self.ffmpeg_binary
        try:
            import imageio_ffmpeg
            return imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            return "ffmpeg"

settings = Settings()
