import os
import math
import struct
import wave
import asyncio
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional

from app.models.api_schemas import VoiceConfig, LanguageCode
from app.config import settings
from app.core.exceptions import ValidationError
from app.core.logger import logger

class TTSAdapterBase(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def licence(self) -> str:
        pass

    @abstractmethod
    async def synthesize(self, text: str, voice_config: VoiceConfig, output_path: str) -> Dict[str, Any]:
        """
        Synthesizes speech audio file and returns {duration, provider, licence, audio_path}.
        """
        pass

class GTTSAdapter(TTSAdapterBase):
    """
    Google Translate TTS adapter (MIT License).
    Supports English, Hindi, and Tamil.
    """
    @property
    def name(self) -> str:
        return "gTTS (Google Translate TTS)"

    @property
    def licence(self) -> str:
        return "MIT License (gTTS Package)"

    async def synthesize(self, text: str, voice_config: VoiceConfig, output_path: str) -> Dict[str, Any]:
        from gtts import gTTS
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        lang_code = voice_config.language.value

        tts = gTTS(text=text, lang=lang_code, slow=voice_config.speech_rate < 0.85)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, tts.save, output_path)

        # Probe duration using wave or ffprobe
        duration = self._probe_duration(output_path)
        return {
            "duration": duration,
            "provider": self.name,
            "licence": self.licence,
            "audio_path": output_path,
            "language": lang_code
        }

    def _probe_duration(self, file_path: str) -> float:
        import subprocess
        ffmpeg_exe = settings.get_ffmpeg_path()
        try:
            cmd = [ffmpeg_exe, "-i", file_path, "-f", "null", "-"]
            res = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, text=True, timeout=10)
            for line in res.stderr.splitlines():
                if "Duration:" in line:
                    parts = line.split("Duration:")[1].split(",")[0].strip()
                    h, m, s = parts.split(":")
                    return round(float(h) * 3600 + float(m) * 60 + float(s), 2)
        except Exception:
            pass
        return 5.0

class EdgeTTSAdapter(TTSAdapterBase):
    """
    Microsoft Edge TTS adapter (MIT License).
    High-fidelity neural voices for EN, HI, TA without paid API keys.
    """
    VOICE_MAP = {
        LanguageCode.EN: "en-US-ChristopherNeural",
        LanguageCode.HI: "hi-IN-MadhurNeural",
        LanguageCode.TA: "ta-IN-ValluvarNeural"
    }

    @property
    def name(self) -> str:
        return "Edge-TTS (Microsoft Neural Voice Engine)"

    @property
    def licence(self) -> str:
        return "MIT License (edge-tts) / Microsoft Speech Service"

    async def synthesize(self, text: str, voice_config: VoiceConfig, output_path: str) -> Dict[str, Any]:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        voice = self.VOICE_MAP.get(voice_config.language, "en-US-ChristopherNeural")
        
        try:
            import edge_tts
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(output_path)
            duration = self._probe_duration(output_path)
            return {
                "duration": duration,
                "provider": self.name,
                "licence": self.licence,
                "audio_path": output_path,
                "language": voice_config.language.value
            }
        except Exception as e:
            logger.warning(f"Edge-TTS synthesis error: {e}. Falling back to GTTSAdapter.")
            return await GTTSAdapter().synthesize(text, voice_config, output_path)

    def _probe_duration(self, file_path: str) -> float:
        import subprocess
        ffmpeg_exe = settings.get_ffmpeg_path()
        try:
            cmd = [ffmpeg_exe, "-i", file_path, "-f", "null", "-"]
            res = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, text=True, timeout=10)
            for line in res.stderr.splitlines():
                if "Duration:" in line:
                    parts = line.split("Duration:")[1].split(",")[0].strip()
                    h, m, s = parts.split(":")
                    return round(float(h) * 3600 + float(m) * 60 + float(s), 2)
        except Exception:
            pass
        return 5.0

class MockTTSAdapter(TTSAdapterBase):
    """
    Zero-API-key test suite mock TTS adapter.
    Accurately records MockTTSAdapter in the manifest and generates valid audible PCM speech.
    """
    @property
    def name(self) -> str:
        return "MockTTSAdapter (Zero-API-Key Test Suite)"

    @property
    def licence(self) -> str:
        return "MIT License (FrameFlow Test Harness)"

    async def synthesize(self, text: str, voice_config: VoiceConfig, output_path: str) -> Dict[str, Any]:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        words = text.split()
        word_count = max(1, len(words))
        base_rate = 2.6 * max(0.5, voice_config.speech_rate)
        duration = max(2.5, round(word_count / base_rate, 2))

        sample_rate = 24000
        total_samples = int(duration * sample_rate)
        f0 = 150.0 + (voice_config.pitch * 8.0)
        if voice_config.language == LanguageCode.HI:
            f0 *= 1.05
        elif voice_config.language == LanguageCode.TA:
            f0 *= 1.02

        wav_path = output_path
        if not wav_path.lower().endswith(".wav"):
            wav_path = str(Path(output_path).with_suffix(".wav"))

        with wave.open(wav_path, "w") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)

            raw_bytes = bytearray()
            for i in range(total_samples):
                t = i / sample_rate
                syllable_mod = 0.5 + 0.5 * math.sin(2 * math.pi * 4.0 * t)
                signal = (
                    0.5 * math.sin(2 * math.pi * f0 * t) +
                    0.3 * math.sin(2 * math.pi * (f0 * 2.2) * t) +
                    0.15 * math.sin(2 * math.pi * (f0 * 3.5) * t)
                ) * syllable_mod

                fade_len = int(sample_rate * 0.05)
                if i < fade_len:
                    signal *= (i / fade_len)
                elif i > total_samples - fade_len:
                    signal *= ((total_samples - i) / fade_len)

                val = int(max(-32767, min(32767, signal * 16000)))
                raw_bytes.extend(struct.pack("<h", val))

            wf.writeframes(raw_bytes)

        if output_path.lower().endswith(".mp3"):
            try:
                import subprocess
                ffmpeg_exe = settings.get_ffmpeg_path()
                subprocess.run(
                    [ffmpeg_exe, "-y", "-i", wav_path, "-codec:a", "libmp3lame", "-b:a", "128k", output_path],
                    check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
            except Exception:
                pass

        return {
            "duration": duration,
            "provider": self.name,
            "licence": self.licence,
            "audio_path": output_path,
            "language": voice_config.language.value
        }

def get_tts_adapter() -> TTSAdapterBase:
    provider = settings.tts_provider.lower()
    if provider == "mock":
        return MockTTSAdapter()
    elif provider == "edge-tts":
        return EdgeTTSAdapter()
    return GTTSAdapter()
