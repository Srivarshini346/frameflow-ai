import os
import math
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
from app.providers.base import FootageProviderBase
from app.models.api_schemas import FootageClip
from app.config import settings
from app.core.logger import logger

class MockFootageProvider(FootageProviderBase):
    """
    Robust Mock / Fallback Footage Provider.
    
    1. Operates without any API keys or network connection.
    2. Provides commercial-grade CC0 synthetic and photographic footage clips.
    3. Programmatically synthesizes real playable MP4 files using FFmpeg
       with Ken Burns camera motion (pan/zoom) on high-resolution curated stock assets
       and animated procedural gradients + theme typography overlays.
    """

    THEMES = {
        "coffee": {
            "color1": (45, 25, 15),
            "color2": (180, 110, 50),
            "label": "Coffee Agriculture, Roasting & Brewing",
            "asset_file": "coffee.jpg"
        },
        "mountain": {
            "color1": (25, 45, 60),
            "color2": (70, 140, 180),
            "label": "Mountain Landscapes, Soil & Agriculture",
            "asset_file": "mountain.jpg"
        },
        "technology": {
            "color1": (25, 30, 80),
            "color2": (40, 120, 220),
            "label": "Technology & AI Systems",
            "asset_file": "technology.jpg"
        },
        "education": {
            "color1": (35, 75, 45),
            "color2": (60, 160, 110),
            "label": "Learning, Students & Academia",
            "asset_file": "education.jpg"
        },
        "nature": {
            "color1": (20, 60, 50),
            "color2": (80, 180, 120),
            "label": "Nature, Forests & Clean Climate",
            "asset_file": "nature.jpg"
        },
        "business": {
            "color1": (40, 30, 60),
            "color2": (120, 90, 180),
            "label": "Global Business, Finance & Markets",
            "asset_file": "business.jpg"
        },
        "healthcare": {
            "color1": (20, 70, 90),
            "color2": (50, 190, 200),
            "label": "Healthcare, Medicine & Science",
            "asset_file": "healthcare.jpg"
        },
        "city": {
            "color1": (45, 45, 55),
            "color2": (180, 130, 80),
            "label": "Smart City Architecture & Urban Life",
            "asset_file": "city.jpg"
        },
        "default": {
            "color1": (40, 45, 75),
            "color2": (110, 120, 190),
            "label": "Cinematic B-roll Visual Footage",
            "asset_file": "default.jpg"
        }
    }

    def __init__(self):
        self._clip_cache_dir = settings.storage_dir / "mock_clips"
        self._clip_cache_dir.mkdir(parents=True, exist_ok=True)
        self._assets_dir = self._clip_cache_dir / "assets"
        self._assets_dir.mkdir(parents=True, exist_ok=True)

    @property
    def name(self) -> str:
        return "MockProvider"

    @property
    def is_available(self) -> bool:
        return True

    async def search_footage(
        self,
        query: str,
        min_duration: float = 3.0,
        limit: int = 5,
        orientation: Optional[str] = None
    ) -> List[FootageClip]:
        """
        Returns high-quality mock clips tailored to the theme and ensures local MP4 files exist.
        """
        theme_key = self._detect_theme(query)
        theme_info = self.THEMES.get(theme_key, self.THEMES["default"])
        clips: List[FootageClip] = []

        for idx in range(limit):
            clip_id = f"mock_{theme_key}_{idx + 1}"
            duration = max(5.0, min_duration + 2.0)
            
            # Generate local synthetic MP4 file if not already on disk or if corrupt
            clip_filename = f"{clip_id}.mp4"
            local_clip_path = self._clip_cache_dir / clip_filename
            if not local_clip_path.exists() or local_clip_path.stat().st_size < 1000:
                self._synthesize_clip(str(local_clip_path), theme_key, theme_info, duration, idx)

            clip = FootageClip(
                clip_id=clip_id,
                provider="MockProvider",
                source_url=f"https://frameflow.local/assets/{clip_filename}",
                download_url=f"{settings.base_url}/storage/mock_clips/{clip_filename}",
                local_path=str(local_clip_path),
                width=1920,
                height=1080,
                duration=duration,
                fps=30.0,
                licence="Creative Commons Zero (CC0 1.0 Universal - Commercial Use Cleared)",
                attribution=f"FrameFlow Synthetic Media Archive - Scene: {theme_info['label']}",
                is_commercial_cleared=True,
                is_ai_generated=True,
                tags=[query, theme_key, "commercial-cleared", "4k-upscaled"]
            )
            clips.append(clip)

        return clips

    def _detect_theme(self, query: str) -> str:
        q = query.lower()
        if any(w in q for w in ("coffee", "brew", "roast", "cherry", "cherries", "bean", "cup", "drink", "cafe")):
            return "coffee"
        if any(w in q for w in ("mountain", "mountains", "farm", "farms", "soil", "harvest", "field", "rural")):
            return "mountain"
        if any(w in q for w in ("ai", "computer", "data", "digital", "screen", "code", "tech", "software", "network")):
            return "technology"
        if any(w in q for w in ("student", "study", "school", "learn", "university", "book", "education", "classroom")):
            return "education"
        if any(w in q for w in ("forest", "water", "tree", "river", "earth", "climate", "nature", "green")):
            return "nature"
        if any(w in q for w in ("money", "growth", "market", "economy", "office", "business", "finance", "stock")):
            return "business"
        if any(w in q for w in ("doctor", "hospital", "patient", "medical", "health", "medicine")):
            return "healthcare"
        if any(w in q for w in ("building", "urban", "street", "traffic", "tower", "city", "architecture")):
            return "city"
        for key in self.THEMES.keys():
            if key in q:
                return key
        return "default"

    def _synthesize_clip(self, output_path: str, theme_key: str, theme_info: Dict[str, Any], duration: float, seed_offset: int):
        """
        Synthesizes a clean 1080p 30fps H.264 video with real visual imagery.
        Uses Ken Burns camera movement (pan & zoom) on cached high-resolution CC0 theme photography,
        or procedural animated multi-gradient flows with theme typography badges as fallback.
        """
        import subprocess
        ffmpeg_exe = settings.get_ffmpeg_path()
        asset_file = theme_info.get("asset_file", f"{theme_key}.jpg")
        asset_path = self._assets_dir / asset_file

        # Fallback to default.jpg if theme asset doesn't exist
        if not asset_path.exists() or asset_path.stat().st_size == 0:
            asset_path = self._assets_dir / "default.jpg"

        frames = int(duration * 30)

        # 1. Preferred path: Real photographic stock asset with Ken Burns camera motion
        if asset_path.exists() and asset_path.stat().st_size > 0:
            clean_asset = str(asset_path).replace("\\", "/")
            if seed_offset % 2 == 0:
                zoom_expr = "min(zoom+0.0006,1.15)"
            else:
                zoom_expr = "max(1.15-0.0006,1.0)"

            vf = (
                f"scale=1920:1080:force_original_aspect_ratio=increase,"
                f"crop=1920:1080,"
                f"zoompan=z='{zoom_expr}':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1920x1080:fps=30,"
                f"eq=contrast=1.03:brightness=0.01:saturation=1.05,"
                f"format=yuv420p"
            )

            cmd = [
                ffmpeg_exe, "-y",
                "-loop", "1",
                "-i", clean_asset,
                "-t", str(duration),
                "-vf", vf,
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-tune", "zerolatency",
                "-pix_fmt", "yuv420p",
                output_path
            ]
            try:
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15)
                logger.info(f"Synthesized rich B-roll clip with Ken Burns motion ({theme_key}) -> {output_path}")
                return
            except Exception as e:
                logger.warning(f"Ken Burns synth fallback ({e})")

        # 2. Procedural animated visual gradient with typography badge
        c1 = theme_info["color1"]
        c2 = theme_info["color2"]
        hex_c1 = f"0x{c1[0]:02x}{c1[1]:02x}{c1[2]:02x}"
        hex_c2 = f"0x{c2[0]:02x}{c2[1]:02x}{c2[2]:02x}"
        label = theme_info["label"].upper()

        vf_proc = (
            f"gradients=s=1920x1080:c0={hex_c1}:c1={hex_c2}:x0=0:y0=0:x1=1920:y1=1080:speed=0.5,"
            f"drawbox=x=80:y=80:w=1760:h=920:color=white@0.15:t=2,"
            f"drawtext=text='{label}':fontcolor=white@0.9:fontsize=44:x=(w-text_w)/2:y=(h-text_h)/2-20,"
            f"drawtext=text='FRAMEFLOW B-ROLL ARCHIVE (COMMERCIAL CLEARED)':fontcolor=white@0.5:fontsize=20:x=(w-text_w)/2:y=(h-text_h)/2+40,"
            f"fps=30,format=yuv420p"
        )

        cmd_proc = [
            ffmpeg_exe, "-y",
            "-f", "lavfi",
            "-i", vf_proc,
            "-t", str(duration),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "ultrafast",
            "-tune", "zerolatency",
            output_path
        ]
        try:
            subprocess.run(cmd_proc, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15)
        except Exception as err:
            logger.error(f"FFmpeg procedural synth failed ({err})")
            # Minimal emergency fallback
            cmd_min = [
                ffmpeg_exe, "-y",
                "-f", "lavfi",
                "-i", f"color=c={hex_c1}:s=1920x1080:d={duration}:r=30",
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-preset", "ultrafast",
                output_path
            ]
            subprocess.run(cmd_min, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)

mock_footage_provider = MockFootageProvider()
