import os
import sys
import secrets
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_STORAGE_DIR = BASE_DIR / "storage"

class Settings(BaseModel):
    app_name: str = "FrameFlow AI – Intelligent B-roll Studio"
    version: str = "1.1.0"
    api_prefix: str = "/api/v1"
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    debug: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")

    # Storage settings
    storage_dir: Path = Path(os.getenv("STORAGE_DIR", str(DEFAULT_STORAGE_DIR)))
    base_url: str = os.getenv("BASE_URL", "http://localhost:8000")

    # S3 / MinIO Configuration
    s3_endpoint_url: Optional[str] = os.getenv("S3_ENDPOINT_URL", None)
    s3_access_key: Optional[str] = os.getenv("S3_ACCESS_KEY", None)
    s3_secret_key: Optional[str] = os.getenv("S3_SECRET_KEY", None)
    s3_bucket_name: str = os.getenv("S3_BUCKET_NAME", "frameflow-deliverables")
    s3_region: str = os.getenv("S3_REGION", "us-east-1")
    s3_use_ssl: bool = os.getenv("S3_USE_SSL", "false").lower() in ("true", "1", "yes")

    # Database Configuration (Postgres or SQLite fallback)
    database_url: str = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_STORAGE_DIR}/frameflow.db")

    # FFmpeg executable
    ffmpeg_binary: str = os.getenv("FFMPEG_BINARY", "")

    # ASR (Transcription) Configuration
    asr_provider: str = os.getenv("ASR_PROVIDER", "mock")  # "faster-whisper" or "mock"
    asr_model_size: str = os.getenv("ASR_MODEL_SIZE", "base")
    asr_device: str = os.getenv("ASR_DEVICE", "cpu")

    # TTS Configuration
    tts_provider: str = os.getenv("TTS_PROVIDER", "gtts")  # "gtts", "edge-tts", or "mock"

    # Relevance Scorer Configuration
    relevance_scorer: str = os.getenv("RELEVANCE_SCORER", "clip")  # "clip" or "mock"

    # Footage Provider API keys (Optional)
    pexels_api_key: str = os.getenv("PEXELS_API_KEY", "")
    pixabay_api_key: str = os.getenv("PIXABAY_API_KEY", "")
    enable_mock_footage: bool = os.getenv("ENABLE_MOCK_FOOTAGE", "true").lower() in ("true", "1", "yes")
    
    # Runtime switch to disable a provider for fallback demonstration (e.g. "pexels,pixabay")
    disable_provider: str = os.getenv("DISABLE_PROVIDER", "")

    # Webhook cryptographic secret (generates ephemeral secret if not provided)
    webhook_secret: str = os.getenv("WEBHOOK_SECRET", "") or secrets.token_hex(24)

    # Concurrency and Scene timing constraints
    max_concurrent_jobs: int = int(os.getenv("MAX_CONCURRENT_JOBS", "4"))
    job_retries: int = int(os.getenv("JOB_RETRIES", "2"))
    min_scene_duration: float = float(os.getenv("MIN_SCENE_DURATION", "2.5"))
    max_scene_duration: float = float(os.getenv("MAX_SCENE_DURATION", "10.0"))
    max_audio_duration_seconds: float = float(os.getenv("MAX_AUDIO_DURATION_SECONDS", "600.0"))  # 10 min max

    # Smart crop method for 9:16 portrait: "saliency" or "center"
    smart_crop_method: str = os.getenv("SMART_CROP_METHOD", "saliency")

    def get_ffmpeg_path(self) -> str:
        if self.ffmpeg_binary and os.path.exists(self.ffmpeg_binary):
            return self.ffmpeg_binary
        try:
            import imageio_ffmpeg
            return imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            return "ffmpeg"

    def is_provider_disabled(self, name: str) -> bool:
        if not self.disable_provider:
            return False
        disabled = [p.strip().lower() for p in self.disable_provider.split(",")]
        return name.lower() in disabled

settings = Settings()
settings.storage_dir.mkdir(parents=True, exist_ok=True)
