from fastapi import APIRouter
from pydantic import BaseModel
from app.models.api_schemas import VoiceConfig, LanguageCode
from app.services.audio_service import audio_service
from app.services.storage_service import storage_service
from app.config import settings
import uuid

router = APIRouter(prefix="/tts", tags=["Speech Synthesis"])

class TTSPreviewRequest(BaseModel):
    text: str
    voice_config: VoiceConfig = VoiceConfig()

@router.post("/synthesize")
async def preview_speech(req: TTSPreviewRequest):
    out_id = f"tts_{uuid.uuid4().hex[:8]}.mp3"
    out_path = str(settings.storage_dir / "previews" / out_id)
    res = await audio_service.generate_speech(req.text, req.voice_config, out_path)
    res["audio_url"] = storage_service.get_public_url(out_path)
    return res
