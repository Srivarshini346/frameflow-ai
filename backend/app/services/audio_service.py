import os
import math
import struct
import wave
from pathlib import Path
from typing import Dict, Any, Optional

from app.models.api_schemas import VoiceConfig
from app.services.tts_service import get_tts_adapter
from app.services.asr_service import validate_audio_file as asr_validate_audio_file
from app.core.exceptions import ValidationError
from app.core.logger import logger

class AudioService:
    """
    Audio orchestrator for speech synthesis and audio validation.
    Delegates TTS to the active TTSAdapter (gTTS / Edge-TTS / MockTTS)
    and audio validation to the strict ASR validation suite.
    """

    def validate_audio_file(self, file_path: str) -> Dict[str, Any]:
        """
        Validates format (.mp3, .wav, .m4a), non-empty, duration <= 600s,
        silence check, and speech vs music-only check.
        """
        return asr_validate_audio_file(file_path)

    async def generate_speech(
        self,
        text: str,
        voice_config: VoiceConfig,
        output_path: str
    ) -> Dict[str, Any]:
        """
        Synthesizes narration speech using the configured TTS adapter.
        """
        if not text or not text.strip():
            raise ValidationError("Cannot synthesize speech from empty text")

        adapter = get_tts_adapter()
        logger.info(f"Synthesizing speech via TTS adapter '{adapter.name}' for language '{voice_config.language.value}'")
        res = await adapter.synthesize(text, voice_config, output_path)
        return res

audio_service = AudioService()
