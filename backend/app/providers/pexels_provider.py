import httpx
from typing import List
from app.providers.base import FootageProviderBase
from app.models.api_schemas import FootageClip
from app.config import settings
from app.core.logger import logger

class PexelsProvider(FootageProviderBase):
    """
    Pexels Video API Adapter.
    Verified commercial use under the Pexels License.
    """
    BASE_URL = "https://api.pexels.com/videos/search"

    @property
    def name(self) -> str:
        return "Pexels"

    @property
    def is_available(self) -> bool:
        return bool(settings.pexels_api_key and settings.pexels_api_key.strip())

    async def search_footage(
        self,
        query: str,
        min_duration: float = 3.0,
        limit: int = 5
    ) -> List[FootageClip]:
        if not self.is_available:
            return []

        headers = {"Authorization": settings.pexels_api_key}
        params = {"query": query, "per_page": limit, "orientation": "landscape"}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(self.BASE_URL, headers=headers, params=params)
                if res.status_code != 200:
                    logger.warning(f"Pexels API responded with status {res.status_code}")
                    return []

                data = res.json()
                videos = data.get("videos", [])
                clips: List[FootageClip] = []

                for v in videos:
                    duration = float(v.get("duration", 0.0))
                    if duration < min_duration:
                        continue

                    # Select best 1080p or 720p MP4 stream
                    video_files = v.get("video_files", [])
                    selected_file = None
                    for vf in video_files:
                        if vf.get("file_type") == "video/mp4":
                            if vf.get("width") == 1920 or vf.get("height") == 1080:
                                selected_file = vf
                                break
                    if not selected_file and video_files:
                        selected_file = video_files[0]

                    if not selected_file:
                        continue

                    user = v.get("user", {})
                    author_name = user.get("name", "Unknown Creator")
                    author_url = user.get("url", "https://pexels.com")

                    clip = FootageClip(
                        clip_id=f"pexels_{v.get('id')}",
                        provider="Pexels",
                        source_url=v.get("url", "https://pexels.com"),
                        download_url=selected_file.get("link", ""),
                        width=selected_file.get("width", 1920),
                        height=selected_file.get("height", 1080),
                        duration=duration,
                        fps=float(selected_file.get("fps", 30.0) or 30.0),
                        licence="Pexels License (Commercial Use Permitted, No Attribution Required)",
                        attribution=f"Video by {author_name} ({author_url}) via Pexels",
                        is_commercial_cleared=True,
                        is_ai_generated=False,
                        tags=[query]
                    )
                    clips.append(clip)

                return clips
        except Exception as e:
            logger.error(f"Error querying Pexels: {e}")
            return []
