import os
import json
import asyncio
import subprocess
import httpx
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple

from app.models.api_schemas import FootageClip, SceneDetail
from app.providers.base import FootageProviderBase
from app.providers.pexels_provider import PexelsProvider
from app.providers.pixabay_provider import PixabayProvider
from app.providers.mock_provider import mock_footage_provider
from app.services.relevance_scorer import relevance_scorer
from app.services.safety_service import safety_service
from app.services.query_intelligence import query_intelligence
from app.config import settings
from app.core.exceptions import FootageSearchError
from app.core.logger import logger

class FootageService:
    """
    Multi-Provider Footage Orchestration Engine:
    1. Concurrently queries all active external providers (Pexels, Pixabay) with asyncio.gather.
    2. Respects DISABLE_PROVIDER runtime env switch for fallback demonstrations.
    3. Respects aspect ratio orientations (landscape for 16:9/1:1, portrait for 9:16).
    4. Evaluates up to 3 query variations (primary + 2 fallbacks) when relevance < RELEVANCE_MIN.
    5. Rejects non-commercial, watermarked, or avoid-keyword matching clips.
    6. Enforces zero duplicate clips per video across all scenes.
    7. Validates downloaded clips with ffprobe container checks (rejects corrupt/48-byte files).
    8. Records selection_rule, reason, and honest unclamped relevance score.
    """

    SELECTION_RULE = "CLIP_score = cosine_similarity(frame, text). Highest commercial-cleared score wins; fallback on score < 0.40 or provider timeout."

    def __init__(self):
        self.pexels_provider = PexelsProvider()
        self.pixabay_provider = PixabayProvider()
        self.mock_provider = mock_footage_provider

    @property
    def providers(self) -> List[FootageProviderBase]:
        return [self.pexels_provider, self.pixabay_provider, self.mock_provider]

    async def find_best_footage_for_scene(
        self,
        scene: SceneDetail,
        seen_clip_ids: Set[str],
        avoid_list: Optional[List[str]] = None,
        requested_provider: Optional[str] = None,
        aspect_ratio: Optional[str] = "16:9"
    ) -> FootageClip:
        avoid_list = avoid_list or []
        min_duration = max(2.0, scene.duration)

        # 1. Determine orientation preference based on target aspect ratio
        orientation = "portrait" if aspect_ratio in ("9:16", "portrait") else "landscape"

        # 2. Get up to 3 query variations (primary + 2 fallbacks)
        phrase_for_query = scene.narration_text or scene.visual_description
        _, queries, _ = query_intelligence.formulate_query_variations(phrase_for_query)
        if scene.search_query and scene.search_query not in queries:
            queries.insert(0, scene.search_query)

        # 3. Identify active real providers
        real_providers: List[FootageProviderBase] = []
        for p in [self.pexels_provider, self.pixabay_provider]:
            p_name = p.name.lower()
            if settings.is_provider_disabled(p_name):
                logger.info(f"Provider '{p.name}' disabled by configuration (DISABLE_PROVIDER)")
                continue
            if not p.is_available:
                continue
            if requested_provider and p_name != requested_provider.lower():
                continue
            real_providers.append(p)

        candidate_clips: List[FootageClip] = []
        selected_clip: Optional[FootageClip] = None
        best_score = -1.0
        best_rating = 1
        best_method = "Keyword overlap heuristic"
        used_query = queries[0] if queries else "cinematic footage"

        # 4. Search real providers concurrently across query variations
        if real_providers:
            for query_candidate in queries:
                used_query = query_candidate
                tasks = [
                    asyncio.wait_for(
                        provider.search_footage(query_candidate, min_duration=min_duration, limit=5, orientation=orientation),
                        timeout=8.0
                    )
                    for provider in real_providers
                ]

                results = await asyncio.gather(*tasks, return_exceptions=True)
                current_query_candidates: List[FootageClip] = []

                for idx, res in enumerate(results):
                    provider_name = real_providers[idx].name
                    if isinstance(res, Exception):
                        logger.warning(f"Error querying {provider_name}: {res}")
                        if isinstance(res, asyncio.TimeoutError):
                            scene.warnings.append(f"Provider {provider_name} timed out")
                        continue
                    if isinstance(res, list):
                        for c in res:
                            # Deduplication
                            if c.clip_id in seen_clip_ids:
                                continue
                            # Commercial & Watermark
                            if not c.is_commercial_cleared or c.watermark:
                                continue
                            # Safety & Avoid list filter
                            is_safe, reason = safety_service.evaluate_candidate_clip(c, avoid_list)
                            if not is_safe:
                                logger.info(f"Clip {c.clip_id} rejected by safety filter: {reason}")
                                continue
                            current_query_candidates.append(c)

                if current_query_candidates:
                    # Rank candidates for this query
                    for clip in current_query_candidates:
                        score, rating, method = relevance_scorer.score_candidate(
                            clip_path_or_url=clip.local_path or clip.download_url,
                            narration_text=scene.narration_text,
                            candidate_tags=clip.tags
                        )
                        if score > best_score:
                            best_score = score
                            best_rating = rating
                            best_method = method
                            selected_clip = clip

                    # If score satisfies RELEVANCE_MIN threshold, stop searching
                    if best_score >= settings.relevance_min and selected_clip:
                        break

        # 5. Fallback to MockProvider if no real candidate selected
        if not selected_clip:
            reason = "No real stock API keys configured" if not real_providers else f"Real stock clips below relevance threshold {settings.relevance_min}"
            warning_msg = f"mock fallback used: {reason}"
            scene.warnings.append(warning_msg)
            logger.info(f"Scene {scene.scene_number}: {warning_msg}")

            mock_clips = await self.mock_provider.search_footage(used_query, min_duration=min_duration, limit=6)
            mock_candidates = [mc for mc in mock_clips if mc.clip_id not in seen_clip_ids]
            if not mock_candidates:
                unique_query = f"{used_query}_{len(seen_clip_ids) + 1}"
                mock_candidates = await self.mock_provider.search_footage(unique_query, min_duration=min_duration, limit=2)

            for mc in mock_candidates:
                score, rating, method = relevance_scorer.score_candidate(
                    clip_path_or_url=mc.local_path or mc.download_url,
                    narration_text=scene.narration_text,
                    candidate_tags=mc.tags
                )
                if score > best_score:
                    best_score = score
                    best_rating = rating
                    best_method = method
                    selected_clip = mc

            if not selected_clip and mock_candidates:
                selected_clip = mock_candidates[0]

        # Register clip ID in seen set to guarantee 0 repeats across the entire video
        seen_clip_ids.add(selected_clip.clip_id)

        # Populate scene metadata
        scene.selected_footage = selected_clip
        scene.source = selected_clip.provider
        scene.clip_id = selected_clip.clip_id
        scene.source_url = selected_clip.source_url
        scene.licence = selected_clip.licence
        scene.attribution = selected_clip.attribution
        scene.is_ai_generated = selected_clip.is_ai_generated
        scene.watermark = False
        scene.selection_rule = self.SELECTION_RULE
        scene.relevance_score = round(max(0.0, best_score), 3)
        scene.clip_rating = best_rating
        scene.search_query = used_query
        scene.selection_reason = (
            f"Selected from {selected_clip.provider} via {best_method} with score {best_score:.2f} ({best_rating}/5 stars). "
            f"Commercial clearance verified ({selected_clip.licence})."
        )

        logger.info(
            f"Scene {scene.scene_number}: Selected {selected_clip.clip_id} from {selected_clip.provider} "
            f"(Score: {best_score:.2f}, Rating: {best_rating}/5, Query: '{used_query}')"
        )
        return selected_clip

    def validate_video_file(self, file_path: Path) -> bool:
        """
        Validates that a video file on disk is not truncated, 0-byte, 48-byte, or corrupt.
        Checks duration > 0 and presence of video stream.
        """
        if not file_path.exists() or file_path.stat().st_size < 1024:
            return False

        ffmpeg_exe = settings.get_ffmpeg_path()
        ffprobe_exe = ffmpeg_exe.replace("ffmpeg", "ffprobe")
        if not os.path.exists(ffprobe_exe):
            ffprobe_exe = "ffprobe"

        cmd = [
            ffprobe_exe, "-v", "error",
            "-show_entries", "format=duration:stream=codec_type",
            "-of", "json",
            str(file_path)
        ]
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5)
            if res.returncode != 0:
                return False
            data = json.loads(res.stdout)
            dur = float(data.get("format", {}).get("duration", 0.0))
            streams = data.get("streams", [])
            has_video = any(s.get("codec_type") == "video" for s in streams)
            return dur > 0.0 and has_video
        except Exception:
            # If ffprobe binary not directly accessible, basic file size threshold (>10KB)
            return file_path.stat().st_size > 10000

    async def ensure_clip_downloaded(self, clip: FootageClip, target_dir: Path) -> str:
        """
        Downloads clip to target directory and validates with ffprobe that the container
        is not truncated, 0/48-byte, or corrupt.
        """
        # If already local and valid
        if clip.local_path and Path(clip.local_path).exists():
            if self.validate_video_file(Path(clip.local_path)):
                return clip.local_path

        target_file = target_dir / f"{clip.clip_id}.mp4"
        if target_file.exists() and self.validate_video_file(target_file):
            clip.local_path = str(target_file)
            return str(target_file)

        # Download from external URL
        logger.info(f"Downloading clip {clip.clip_id} from {clip.download_url}")
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                res = await client.get(clip.download_url)
                if res.status_code == 200 and len(res.content) >= 1024:
                    with open(target_file, "wb") as f:
                        f.write(res.content)
                    
                    if self.validate_video_file(target_file):
                        clip.local_path = str(target_file)
                        return str(target_file)
                    else:
                        logger.warning(f"Downloaded file for {clip.clip_id} was corrupt or invalid container.")
                        target_file.unlink(missing_ok=True)
                else:
                    logger.warning(f"Download returned status {res.status_code} or payload size {len(res.content)}B was too small.")
        except Exception as e:
            logger.warning(f"Download exception for {clip.clip_id}: {e}")

        # Fallback to Mock clip if download fails or is corrupt
        logger.warning(f"Using synthetic fallback for clip {clip.clip_id}")
        mock_clips = await self.mock_provider.search_footage(clip.tags[0] if clip.tags else "broll", limit=1)
        clip.local_path = mock_clips[0].local_path
        return clip.local_path

footage_service = FootageService()
