import re
from typing import List
from pathlib import Path
from app.models.api_schemas import SceneDetail, CaptionConfig

class CaptionService:
    """
    Handles SRT subtitle generation, ASS styling, and caption burning filters.
    """

    def generate_srt(self, scenes: List[SceneDetail], output_path: str) -> str:
        """
        Creates a standard compliant SubRip (.srt) subtitle file with sub-second precision.
        """
        srt_lines: List[str] = []
        for i, sc in enumerate(scenes):
            index = i + 1
            start_fmt = self._seconds_to_srt_time(sc.start_time)
            end_fmt = self._seconds_to_srt_time(sc.end_time)
            text = sc.narration_text.strip()
            srt_lines.append(f"{index}\n{start_fmt} --> {end_fmt}\n{text}\n")

        content = "\n".join(srt_lines)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        return output_path

    def _seconds_to_srt_time(self, seconds: float) -> str:
        hrs = int(seconds // 3600)
        rem = seconds % 3600
        mins = int(rem // 60)
        secs = int(rem % 60)
        millis = int(round((seconds - int(seconds)) * 1000))
        return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"

    def build_subtitle_filter(
        self,
        srt_path: str,
        caption_config: CaptionConfig,
        aspect_ratio: str
    ) -> str:
        """
        Builds FFmpeg subtitle filter with responsive font sizing and background styling.
        Escapes Windows backslashes and colons properly for FFmpeg.
        """
        escaped_path = srt_path.replace("\\", "/").replace(":", "\\:")
        
        # Adjust font size for vertical portrait vs landscape
        size = caption_config.font_size
        if aspect_ratio == "9:16":
            size = int(size * 1.3)
        elif aspect_ratio == "1:1":
            size = int(size * 1.1)

        style = (
            f"FontSize={size},"
            f"PrimaryColour=&H00FFFFFF,"
            f"OutlineColour=&H00000000,"
            f"BackColour=&H80000000,"
            f"BorderStyle=3,"
            f"Outline=1,"
            f"Shadow=0,"
            f"Alignment=2,"
            f"MarginV=40"
        )
        return f"subtitles='{escaped_path}':force_style='{style}'"

caption_service = CaptionService()
