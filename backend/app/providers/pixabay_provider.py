import httpx
from typing import List, Optional, Tuple
from app.providers.base import FootageProviderBase
from app.models.api_schemas import FootageClip
from app.config import settings
from app.core.logger import logger

class PixabayProvider(FootageProviderBase):
    """
    Pixabay Video API Adapter.
    Verified commercial use under Pixabay Content License.
    """
    BASE_URL = "https://pixabay.com/api/videos/"

    @property
    def name(self) -> str:
        return "Pixabay"

    @property
    def is_available(self) -> bool:
        return bool(settings.pixabay_api_key and settings.pixabay_api_key.strip())

    async def check_active_status(self) -> Tuple[bool, str]:
        if not self.is_available:
            return False, "No key configured"
        try:
            params = {
                "key": settings.pixabay_api_key,
                "q": "nature",
                "per_page": 3
            }
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.get(self.BASE_URL, params=params)
                if res.status_code == 200:
                    return True, "Active"
                elif res.status_code in (400, 401, 403):
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

        params = {
            "key": settings.pixabay_api_key,
            "q": query,
            "per_page": limit,
            "safesearch": "true"
        }
        if orientation:
            if orientation == "portrait":
                params["orientation"] = "vertical"
            elif orientation == "landscape":
                params["orientation"] = "horizontal"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(self.BASE_URL, params=params)
                if res.status_code != 200:
                    logger.warning(f"Pixabay API error: {res.status_code}")
                    return []

                data = res.json()
                hits = data.get("hits", [])
                clips: List[FootageClip] = []

                for hit in hits:
                    duration = float(hit.get("duration", 0.0))
                    if duration < min_duration:
                        continue

                    videos_dict = hit.get("videos", {})
                    # Prefer large or medium
                    target_stream = videos_dict.get("large") or videos_dict.get("medium") or videos_dict.get("small")
                    if not target_stream or not target_stream.get("url"):
                        continue

                    author = hit.get("user", "Unknown Artist")
                    page_url = hit.get("pageURL", "https://pixabay.com")

                    # Extract tags
                    tags_raw = hit.get("tags", "")
                    tags_list = [t.strip().lower() for t in tags_raw.split(",") if t.strip()]
                    if query not in tags_list:
                        tags_list.insert(0, query)

                    clip = FootageClip(
                        clip_id=f"pixabay_{hit.get('id')}",
                        provider="Pixabay",
                        source_url=page_url,
                        download_url=target_stream.get("url"),
                        width=target_stream.get("width", 1920),
                        height=target_stream.get("height", 1080),
                        duration=duration,
                        fps=30.0,
                        licence="Pixabay Content License (Commercial Use Allowed, Attribution Appreciated)",
                        attribution=f"Video by {author} from Pixabay",
                        is_commercial_cleared=True,
                        is_ai_generated=False,
                        tags=tags_list
                    )
                    clips.append(clip)

                return clips
        except Exception as e:
            logger.error(f"Error querying Pixabay: {e}")
            return []
