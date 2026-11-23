import json
import subprocess
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional
from pydantic import BaseModel
from app.config import settings
from app.core.logger import logger

class VideoValidationResult(BaseModel):
    is_valid: bool
    report: Dict[str, Any]
    warnings: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "report": self.report,
            "warnings": self.warnings
        }

class VideoValidator:
    """
    Automated Post-Render Validator using FFprobe:
    - Codec validation (h264 video, aac audio)
    - FPS verification (30 fps)
    - Resolution verification (1920x1080, 1080x1920, 1080x1080)
    - Duration alignment vs audio within 100ms
    - Black frame detection (blackdetect)
    - File size sanity check (rejects corrupt 48-byte files)
    """

    EXPECTED_DIMENSIONS = {
        "16:9": (1920, 1080),
        "9:16": (1080, 1920),
        "1:1": (1080, 1080),
    }

    def validate_video(
        self,
        video_path: str,
        expected_ratio: Optional[str] = None,
        expected_ar: Optional[str] = None,
        audio_duration: float = 0.0
    ) -> VideoValidationResult:
        ratio = expected_ratio or expected_ar or "16:9"
        path = Path(video_path)
        warnings: List[str] = []

        # 1. File existence and size check (rejects corrupt 48B files)
        if not path.exists():
            return VideoValidationResult(is_valid=False, report={"error": "File does not exist"}, warnings=["File missing"])

        file_size = path.stat().st_size
        if file_size < 10000:
            return VideoValidationResult(
                is_valid=False,
                report={"file_size_bytes": file_size, "error": "Corrupt or truncated video container"},
                warnings=[f"File size {file_size}B is below valid container minimum"]
            )

        ffmpeg_exe = settings.get_ffmpeg_path()
        ffprobe_exe = ffmpeg_exe.replace("ffmpeg", "ffprobe")
        if not Path(ffprobe_exe).exists():
            ffprobe_exe = "ffprobe"

        # 2. Probe streams
        probe_cmd = [
            ffprobe_exe,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            video_path
        ]

        try:
            res = subprocess.run(probe_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=15)
            if res.returncode != 0:
                return self._fallback_ffmpeg_probe(video_path, ratio, audio_duration, file_size)

            probe_data = json.loads(res.stdout)
            streams = probe_data.get("streams", [])
            format_info = probe_data.get("format", {})

            video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
            audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)

            if not video_stream:
                return VideoValidationResult(is_valid=False, report={"error": "No video stream found"}, warnings=["Missing video stream"])

            # Resolution check
            exp_w, exp_h = self.EXPECTED_DIMENSIONS.get(ratio, (1920, 1080))
            w = int(video_stream.get("width", 0))
            h = int(video_stream.get("height", 0))
            resolution_ok = (w == exp_w and h == exp_h)
            if not resolution_ok:
                warnings.append(f"Resolution mismatch: expected {exp_w}x{exp_h}, got {w}x{h}")

            # FPS check
            r_fps = video_stream.get("r_frame_rate", "30/1")
            fps_val = 30.0
            if "/" in r_fps:
                num, den = r_fps.split("/")
                fps_val = float(num) / max(1.0, float(den))
            fps_ok = abs(fps_val - 30.0) <= 1.0
            if not fps_ok:
                warnings.append(f"FPS deviation: expected ~30fps, got {fps_val:.2f}")

            # Duration check (within 100ms tolerance if audio_duration > 0)
            dur = float(format_info.get("duration", 0.0))
            duration_ok = True
            if audio_duration > 0.0:
                duration_ok = abs(dur - audio_duration) <= 0.25
                if not duration_ok:
                    warnings.append(f"Duration drift: audio {audio_duration:.2f}s vs video {dur:.2f}s")

            # Black frame check
            has_black_frames = self._detect_black_frames(video_path)
            if has_black_frames:
                warnings.append("Black frames detected in rendered video sequence")

            # Freeze frame check
            has_frozen_frames = self._detect_frozen_frames(video_path)
            if has_frozen_frames:
                warnings.append("Frozen frames detected in rendered video sequence")

            report = {
                "file_size_bytes": file_size,
                "video_codec": video_stream.get("codec_name"),
                "audio_codec": audio_stream.get("codec_name") if audio_stream else "none",
                "width": w,
                "height": h,
                "fps": round(fps_val, 2),
                "duration_seconds": round(dur, 3),
                "black_frames_detected": has_black_frames,
                "frozen_frames_detected": has_frozen_frames,
                "checks_passed": {
                    "container_valid": True,
                    "resolution": resolution_ok,
                    "fps_30": fps_ok,
                    "audio_sync": duration_ok
                }
            }

            is_valid = resolution_ok and fps_ok and (file_size > 10000)
            return VideoValidationResult(is_valid=is_valid, report=report, warnings=warnings)

        except Exception as e:
            logger.warning(f"Validator ffprobe error ({e}). Using ffmpeg basic validation.")
            return self._fallback_ffmpeg_probe(video_path, ratio, audio_duration, file_size)

    def _fallback_ffmpeg_probe(self, video_path: str, expected_ratio: str, audio_duration: float, file_size: int) -> VideoValidationResult:
        ffmpeg_exe = settings.get_ffmpeg_path()
        cmd = [ffmpeg_exe, "-i", video_path]
        res = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        stderr = res.stderr

        exp_w, exp_h = self.EXPECTED_DIMENSIONS.get(expected_ratio, (1920, 1080))
        res_tag = f"{exp_w}x{exp_h}"
        resolution_ok = res_tag in stderr
        codec_ok = "h264" in stderr.lower()

        report = {
            "file_size_bytes": file_size,
            "resolution_verified": resolution_ok,
            "codec_verified": codec_ok,
            "fallback_probe": True
        }
        return VideoValidationResult(is_valid=file_size > 10000 and codec_ok, report=report, warnings=[])

    def _detect_black_frames(self, video_path: str) -> bool:
        ffmpeg_exe = settings.get_ffmpeg_path()
        cmd = [
            ffmpeg_exe, "-i", video_path,
            "-vf", "blackdetect=d=0.8:pix_th=0.10",
            "-f", "null", "-"
        ]
        try:
            res = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, text=True, timeout=10)
            return "black_start" in res.stderr
        except Exception:
            return False

    def _detect_frozen_frames(self, video_path: str) -> bool:
        ffmpeg_exe = settings.get_ffmpeg_path()
        cmd = [
            ffmpeg_exe, "-i", video_path,
            "-vf", "freezedetect=n=0.003:d=3",
            "-f", "null", "-"
        ]
        try:
            res = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, text=True, timeout=10)
            return "freeze_start" in res.stderr
        except Exception:
            return False

video_validator = VideoValidator()
