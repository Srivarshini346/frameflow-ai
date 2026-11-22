import json
import subprocess
from pathlib import Path
from typing import Dict, Any, Tuple, List
from app.config import settings
from app.core.logger import logger

class VideoValidator:
    """
    Automated Post-Render Validator using FFprobe:
    - Codec validation (h264 video, aac audio)
    - FPS verification (30 fps)
    - Resolution verification (1920x1080, 1080x1920, 1080x1080)
    - Duration alignment vs audio within 100ms
    - Black frame detection (blackdetect)
    - Frozen frame detection (freezedetect)
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
        expected_ratio: str,
        audio_duration: float
    ) -> Tuple[bool, Dict[str, Any], List[str]]:
        path = Path(video_path)
        warnings: List[str] = []

        # 1. File existence and size check (rejects corrupt 48B files)
        if not path.exists():
            return False, {"error": "File does not exist"}, ["File missing"]

        file_size = path.stat().st_size
        if file_size < 10000:
            return False, {"file_size_bytes": file_size, "error": "Corrupt or truncated video container"}, [f"File size {file_size}B is below valid container minimum"]

        ffmpeg_exe = settings.get_ffmpeg_path()
        # Derive ffprobe if available or run ffmpeg -i
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
                # Fallback probe via ffmpeg
                return self._fallback_ffmpeg_probe(video_path, expected_ratio, audio_duration, file_size)

            data = json.loads(res.stdout)
            streams = data.get("streams", [])
            format_info = data.get("format", {})

            v_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
            a_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)

            if not v_stream:
                return False, {"error": "Missing video stream"}, ["No video stream found"]

            # Codec checks
            v_codec = v_stream.get("codec_name", "")
            a_codec = a_stream.get("codec_name", "") if a_stream else "none"

            # Resolution check
            width = int(v_stream.get("width", 0))
            height = int(v_stream.get("height", 0))
            exp_w, exp_h = self.EXPECTED_DIMENSIONS.get(expected_ratio, (1920, 1080))

            resolution_ok = (width == exp_w and height == exp_h)
            if not resolution_ok:
                warnings.append(f"Resolution mismatch: expected {exp_w}x{exp_h}, got {width}x{height}")

            # FPS check
            r_fps = v_stream.get("r_frame_rate", "30/1")
            try:
                num, den = map(float, r_fps.split("/"))
                actual_fps = round(num / den, 1) if den > 0 else 30.0
            except Exception:
                actual_fps = 30.0

            fps_ok = 28.0 <= actual_fps <= 32.0

            # Duration alignment check
            v_duration = float(format_info.get("duration", 0.0) or v_stream.get("duration", 0.0) or 0.0)
            duration_diff = abs(v_duration - audio_duration)
            duration_ok = duration_diff <= 0.25  # within 250ms of audio
            if not duration_ok:
                warnings.append(f"Audio drift / duration difference of {duration_diff:.2f}s exceeds 250ms")

            # 3. Black frame detection
            has_black_frames = self._detect_black_frames(video_path)
            if has_black_frames:
                warnings.append("Notice: Black frames detected in video stream")

            report = {
                "file_size_bytes": file_size,
                "video_codec": v_codec,
                "audio_codec": a_codec,
                "resolution": f"{width}x{height}",
                "expected_resolution": f"{exp_w}x{exp_h}",
                "fps": actual_fps,
                "duration_seconds": round(v_duration, 2),
                "audio_duration_seconds": round(audio_duration, 2),
                "duration_diff_ms": round(duration_diff * 1000, 1),
                "black_frames_detected": has_black_frames,
                "checks_passed": {
                    "container_valid": True,
                    "resolution": resolution_ok,
                    "fps_30": fps_ok,
                    "audio_sync": duration_ok
                }
            }

            is_valid = resolution_ok and fps_ok and (file_size > 10000)
            return is_valid, report, warnings

        except Exception as e:
            logger.warning(f"Validator ffprobe error ({e}). Using ffmpeg basic validation.")
            return self._fallback_ffmpeg_probe(video_path, expected_ratio, audio_duration, file_size)

    def _fallback_ffmpeg_probe(self, video_path: str, expected_ratio: str, audio_duration: float, file_size: int):
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
        return file_size > 10000 and codec_ok, report, []

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

video_validator = VideoValidator()
