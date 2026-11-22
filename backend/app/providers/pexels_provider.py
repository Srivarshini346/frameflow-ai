import httpx
from typing import List, Optional, Tuple
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

    async def check_active_status(self) -> Tuple[bool, str]:
        if not self.is_available:
            return False, "No key configured"
        try:
            headers = {"Authorization": settings.pexels_api_key}
            params = {"query": "nature", "per_page": 1}
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.get(self.BASE_URL, headers=headers, params=params)
                if res.status_code == 200:
                    return True, "Active"
                elif res.status_code in (401, 403):
                    return False, "Invalid API key"
                else:
                    return False, f"API error ({res.status_code})"
        except Exception as e:
            return False, f"Connection error: {str(e)[:30]}"

    async def search_footage(
        self,
        query: str,
        min_duration: float = 3.0,
        limit: int = 5,
        orientation: Optional[str] = None
    ) -> List[FootageClip]:
        if not self.is_available:
            return []

        headers = {"Authorization": settings.pexels_api_key}
        params = {"query": query, "per_page": limit}
        if orientation:
            params["orientation"] = orientation  # "landscape", "portrait", or "square"

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

                    # Select best stream: prefer MP4 with height >= 1080 (1080p), fallback to >= 720, then any MP4
                    video_files = v.get("video_files", [])
                    mp4_files = [f for f in video_files if f.get("file_type") == "video/mp4" and f.get("link")]
                    if not mp4_files:
                        continue

                    # Sort by resolution: height descending
                    mp4_files.sort(key=lambda x: int(x.get("height") or 0), reverse=True)
                    
                    selected_file = None
                    for f in mp4_files:
                        h = int(f.get("height") or 0)
                        if h >= 1080:
                            selected_file = f
                            break
                    if not selected_file:
                        for f in mp4_files:
                            h = int(f.get("height") or 0)
                            if h >= 720:
                                selected_file = f
                                break
                    if not selected_file and mp4_files:
                        selected_file = mp4_files[0]

                    if not selected_file:
                        continue

                    user = v.get("user", {})
                    author_name = user.get("name", "Unknown Creator")
                    author_url = user.get("url", "https://pexels.com")
                    
                    # Extract tags or video description if available
                    clip_tags = [query]
                    if v.get("tags"):
                        clip_tags.extend([t.get("name", "") if isinstance(t, dict) else str(t) for t in v.get("tags", [])])

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
                        tags=list(set(filter(None, clip_tags)))
                    )
                    clips.append(clip)

                return clips
        except Exception as e:
            logger.error(f"Error querying Pexels: {e}")
            return []
