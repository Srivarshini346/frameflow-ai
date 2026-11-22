import httpx
from typing import List, Dict, Any, Optional, Set
from pathlib import Path
from app.models.api_schemas import FootageClip, SceneDetail
from app.providers.base import FootageProviderBase
from app.providers.pexels_provider import PexelsProvider
from app.providers.pixabay_provider import PixabayProvider
from app.providers.mock_provider import mock_footage_provider
from app.services.vlm_service import vlm_service
from app.config import settings
from app.core.logger import logger

class FootageService:
    """
    Orchestrates multiple footage providers, enforces zero duplicate clips,
    evaluates semantic & VLM relevance, and verifies commercial licensing.
    """

    def __init__(self):
        self.providers: List[FootageProviderBase] = [
            PexelsProvider(),
            PixabayProvider(),
            mock_footage_provider
        ]

    async def find_best_footage_for_scene(
        self,
        scene: SceneDetail,
        seen_clip_ids: Set[str],
        requested_provider: Optional[str] = None
    ) -> FootageClip:
        """
        Finds the highest-scoring unique commercial clip for a scene,
        falling back through providers and preventing duplicate clips.
        """
        query = scene.search_query or scene.visual_description
        min_duration = max(2.0, scene.duration)

        candidate_clips: List[FootageClip] = []

        # 1. Query available external providers first (if configured)
        for provider in self.providers:
            if not provider.is_available:
                continue
            if requested_provider and provider.name.lower() != requested_provider.lower():
                continue

            try:
                clips = await provider.search_footage(query, min_duration=min_duration, limit=4)
                for c in clips:
                    if c.clip_id not in seen_clip_ids:
                        candidate_clips.append(c)
                if candidate_clips:
                    break
            except Exception as e:
                logger.warning(f"Provider {provider.name} failed for query '{query}': {e}. Trying fallback.")

        # 2. If no candidate clips found, use MockFootageProvider fallback
        if not candidate_clips:
            mock_clips = await mock_footage_provider.search_footage(query, min_duration=min_duration, limit=6)
            for mc in mock_clips:
                if mc.clip_id not in seen_clip_ids:
                    candidate_clips.append(mc)

        # 3. If still empty (all mock clips used), synthesize a dedicated fresh unique clip
        if not candidate_clips:
            unique_query = f"{query}_{len(seen_clip_ids) + 1}"
            mock_clips = await mock_footage_provider.search_footage(unique_query, min_duration=min_duration, limit=2)
            candidate_clips.extend(mock_clips)

        # 4. Rank candidates by VLM & Semantic Relevance
        best_clip = candidate_clips[0]
        best_relevance = 0.0
        best_vlm = 0.0
        best_reason = ""

        for clip in candidate_clips:
            rel, vlm, reason = vlm_service.compute_semantic_relevance(
                scene_visual_desc=scene.visual_description,
                narration_text=scene.narration_text,
                clip=clip
            )
            if rel >= best_relevance:
                best_relevance = rel
                best_vlm = vlm
                best_reason = reason
                best_clip = clip

        # Register clip ID in seen set to prevent duplicate clips in this video
        seen_clip_ids.add(best_clip.clip_id)

        # Update scene metadata
        scene.relevance_score = best_relevance
        scene.vlm_score = best_vlm
        scene.selection_reason = best_reason
        scene.selected_footage = best_clip

        logger.info(
            f"Scene {scene.scene_number}: Matched clip {best_clip.clip_id} from {best_clip.provider} "
            f"(Score: {best_relevance}, VLM: {best_vlm})"
        )
        return best_clip

    async def ensure_clip_downloaded(self, clip: FootageClip, target_dir: Path) -> str:
        """
        Ensures the video file exists locally on disk for FFmpeg rendering.
        """
        if clip.local_path and Path(clip.local_path).exists() and Path(clip.local_path).stat().st_size > 0:
            return clip.local_path

        target_file = target_dir / f"{clip.clip_id}.mp4"
        if target_file.exists() and target_file.stat().st_size > 0:
            clip.local_path = str(target_file)
            return str(target_file)

        # Download from external URL
        logger.info(f"Downloading clip {clip.clip_id} from {clip.download_url}")
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            res = await client.get(clip.download_url)
            if res.status_code == 200:
                with open(target_file, "wb") as f:
                    f.write(res.content)
                clip.local_path = str(target_file)
                return str(target_file)
            else:
                logger.warning(f"Download failed for {clip.clip_id} ({res.status_code}). Generating synthetic fallback.")
                mock_clips = await mock_footage_provider.search_footage(clip.tags[0] if clip.tags else "broll", limit=1)
                clip.local_path = mock_clips[0].local_path
                return clip.local_path

footage_service = FootageService()
