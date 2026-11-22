import os
try:
    import psutil
except ImportError:
    psutil = None
from fastapi import APIRouter
from app.config import settings
from app.services.footage_service import footage_service

router = APIRouter(prefix="/analytics", tags=["Analytics & Providers"])

@router.get("")
async def get_analytics():
    providers_info = []
    for p in footage_service.providers:
        is_active, status_msg = await p.check_active_status()
        providers_info.append({
            "name": p.name,
            "is_available": p.is_available,
            "is_active": is_active,
            "status": status_msg,
            "type": "api" if "Mock" not in p.name else "synthetic_cc0",
            "commercial_cleared": True
        })

    # System resource metrics
    mem = psutil.virtual_memory() if hasattr(psutil, "virtual_memory") else None

    return {
        "engine": "FrameFlow AI Intelligent B-roll Engine",
        "version": settings.version,
        "providers": providers_info,
        "supported_aspect_ratios": ["16:9", "9:16", "1:1"],
        "supported_languages": ["en (English)", "hi (Hindi)", "ta (Tamil)"],
        "system_resources": {
            "storage_dir": str(settings.storage_dir),
            "ffmpeg_path": settings.get_ffmpeg_path(),
            "memory_usage_percent": mem.percent if mem else "N/A"
        },
        "licensing_policy": {
            "strict_commercial_only": True,
            "supported_licenses": ["Creative Commons Zero (CC0)", "Pexels License", "Pixabay License"],
            "prevent_duplicates": True
        }
    }
