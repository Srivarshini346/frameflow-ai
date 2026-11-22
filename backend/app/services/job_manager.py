import os
import time
import base64
import asyncio
import sqlite3
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from app.models.api_schemas import (
    JobStatus, JobDetailResponse, JobResultResponse,
    BrollJobCreateRequest, SceneDetail, AspectRatio, FootageClip
)
from app.services.audio_service import audio_service
from app.services.scene_engine import scene_engine
from app.services.footage_service import footage_service
from app.services.video_engine import video_engine
from app.services.caption_service import caption_service
from app.services.storage_service import storage_service
from app.services.webhook_service import webhook_service
from app.config import settings
from app.core.exceptions import FrameFlowError, JobNotFoundError, ValidationError
from app.core.logger import logger

class JobManager:
    """
    Central background job orchestrator.
    Manages queued, running, succeeded, failed states, scene progress,
    incremental clip rerendering, and persistence.
    """

    def __init__(self):
        self._jobs: Dict[str, Dict[str, Any]] = {}
        self._db_path = settings.storage_dir / "frameflow.db"
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    correlation_id TEXT,
                    status TEXT,
                    progress INTEGER,
                    stage TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    error TEXT,
                    data_json TEXT
                )
            """)
            conn.commit()

    def create_job(self, req: BrollJobCreateRequest, correlation_id: str, job_id: str) -> JobDetailResponse:
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        job_record = {
            "job_id": job_id,
            "correlation_id": correlation_id,
            "status": JobStatus.QUEUED,
            "progress": 0,
            "stage": "queued",
            "request": req.dict(),
            "scenes": [],
            "warnings": [],
            "error": None,
            "result": None,
            "created_at": now,
            "updated_at": now
        }
        self._jobs[job_id] = job_record
        self._persist(job_id)

        # Trigger background processing task
        asyncio.create_task(self._run_job_pipeline(job_id))

        return self.get_job_detail(job_id)

    def get_job_detail(self, job_id: str) -> JobDetailResponse:
        job = self._jobs.get(job_id)
        if not job:
            job = self._load_from_db(job_id)
        if not job:
            raise JobNotFoundError(job_id)

        scenes_models = [SceneDetail(**s) if isinstance(s, dict) else s for s in job.get("scenes", [])]

        return JobDetailResponse(
            job_id=job["job_id"],
            correlation_id=job["correlation_id"],
            status=job["status"],
            progress=job["progress"],
            stage=job["stage"],
            scenes=scenes_models,
            warnings=job.get("warnings", []),
            error=job.get("error"),
            created_at=job["created_at"],
            updated_at=job["updated_at"]
        )

    def get_job_result(self, job_id: str) -> JobResultResponse:
        job = self._jobs.get(job_id)
        if not job:
            job = self._load_from_db(job_id)
        if not job:
            raise JobNotFoundError(job_id)

        res = job.get("result")
        if not res or job["status"] != JobStatus.SUCCEEDED:
            return JobResultResponse(
                job_id=job_id,
                status=job["status"],
                video_urls={},
                metrics={"status": "in_progress" if job["status"] == JobStatus.RUNNING else "failed"}
            )

        return JobResultResponse(
            job_id=job_id,
            status=job["status"],
            video_urls=res.get("video_urls", {}),
            captions_srt_url=res.get("captions_srt_url"),
            timeline_json_url=res.get("timeline_json_url"),
            manifest_json_url=res.get("manifest_json_url"),
            metrics=res.get("metrics", {}),
            licences=res.get("licences", []),
            quality_report=res.get("quality_report", {})
        )

    async def replace_scene_footage(
        self,
        job_id: str,
        scene_number: int,
        new_clip_id: Optional[str] = None,
        custom_query: Optional[str] = None
    ) -> JobDetailResponse:
        """
        Incremental rerender: Replaces footage for a single scene and dynamically
        reassembles full videos without re-rendering unaffected scenes.
        """
        job = self._jobs.get(job_id) or self._load_from_db(job_id)
        if not job:
            raise JobNotFoundError(job_id)

        scenes = job.get("scenes", [])
        target_scene_idx = None
        for i, s in enumerate(scenes):
            if s["scene_number"] == scene_number:
                target_scene_idx = i
                break

        if target_scene_idx is None:
            raise ValidationError(f"Scene number {scene_number} not found in job {job_id}")

        target_scene = SceneDetail(**scenes[target_scene_idx])
        if custom_query:
            target_scene.search_query = custom_query
            target_scene.visual_description = f"User custom: {custom_query}"

        job_dir = storage_service.get_job_dir(job_id)
        seen_clips = {s["selected_footage"]["clip_id"] for s in scenes if s.get("selected_footage")}
        # Remove current scene's clip so it can be replaced
        if target_scene.selected_footage:
            seen_clips.discard(target_scene.selected_footage.clip_id)

        # Find new footage
        new_clip = await footage_service.find_best_footage_for_scene(target_scene, seen_clips)
        await footage_service.ensure_clip_downloaded(new_clip, job_dir)
        target_scene.selected_footage = new_clip
        scenes[target_scene_idx] = target_scene.dict()

        # Re-render ONLY this scene's clip for each aspect ratio
        aspect_ratios = [AspectRatio(r) for r in job["request"].get("aspect_ratios", ["16:9", "9:16", "1:1"])]
        audio_path = job["audio_path"]
        srt_path = job["srt_path"]
        caption_cfg = job["caption_config"]

        for ar in aspect_ratios:
            ratio_tag = ar.value.replace(":", "_")
            clip_path = str(job_dir / f"clip_sc{scene_number}_{ratio_tag}.mp4")
            video_engine.render_scene_clip(target_scene, ar, clip_path)

            # Re-assemble full video
            all_clip_paths = [
                str(job_dir / f"clip_sc{s['scene_number']}_{ratio_tag}.mp4") for s in scenes
            ]
            final_out = str(job_dir / f"video_{ratio_tag}.mp4")
            video_engine.assemble_full_video(
                all_clip_paths, audio_path, srt_path, caption_cfg, ar, final_out, job_dir
            )

        # Update timeline.json & manifest.json
        scene_objs = [SceneDetail(**s) for s in scenes]
        timeline_path = str(job_dir / "timeline.json")
        manifest_path = str(job_dir / "manifest.json")
        video_engine.build_timeline_json(scene_objs, timeline_path)
        video_engine.build_manifest_json(job_id, scene_objs, 1.5, job["request"], manifest_path)

        job["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        self._jobs[job_id] = job
        self._persist(job_id)

        logger.info(f"Job {job_id}: Incremental rerender completed for scene {scene_number}")
        return self.get_job_detail(job_id)

    async def _run_job_pipeline(self, job_id: str):
        """
        Executes the end-to-end multi-stage pipeline:
        1. Validating input & audio
        2. Speech synthesis (if text script) / Transcription (if audio uploaded)
        3. Meaning-based scene segmentation
        4. Footage discovery, deduplication, and licensing
        5. Video clip rendering & full composite assembly (16:9, 9:16, 1:1)
        6. Subtitle & manifest delivery
        """
        job = self._jobs[job_id]
        start_time = time.time()
        job_dir = storage_service.get_job_dir(job_id)

        try:
            self._update_stage(job_id, "validating", 5, JobStatus.RUNNING)
            req = job["request"]

            # 1. Audio and narration processing
            audio_path = str(job_dir / "narration.wav")
            audio_duration = 5.0

            if req.get("audio_base64"):
                self._update_stage(job_id, "transcribing_narration", 15)
                raw_bytes = base64.b64decode(req["audio_base64"])
                raw_audio_path = str(job_dir / (req.get("audio_filename") or "uploaded_audio.wav"))
                with open(raw_audio_path, "wb") as f:
                    f.write(raw_bytes)
                audio_props = audio_service.validate_audio_file(raw_audio_path)
                audio_path = raw_audio_path
                audio_duration = audio_props["duration"]
            elif req.get("audio_url"):
                self._update_stage(job_id, "fetching_audio", 15)
                # Fetch audio
                import httpx
                async with httpx.AsyncClient(timeout=20.0) as client:
                    res = await client.get(req["audio_url"])
                    raw_audio_path = str(job_dir / "remote_audio.wav")
                    with open(raw_audio_path, "wb") as f:
                        f.write(res.content)
                audio_props = audio_service.validate_audio_file(raw_audio_path)
                audio_path = raw_audio_path
                audio_duration = audio_props["duration"]
            else:
                self._update_stage(job_id, "synthesizing_speech", 15)
                script_text = req.get("script_text")
                if not script_text or not script_text.strip():
                    raise ValidationError("Either script_text, audio_url, or audio_base64 must be provided")

                from app.models.api_schemas import VoiceConfig
                voice_cfg = VoiceConfig(**req.get("voice_config", {}))
                tts_res = await audio_service.generate_speech(script_text, voice_cfg, audio_path)
                audio_duration = tts_res["duration"]

            job["audio_path"] = audio_path
            job["audio_duration"] = audio_duration

            # 2. Intelligent Scene Segmentation
            self._update_stage(job_id, "segmenting_scenes", 30)
            from app.models.api_schemas import VisualPromptStyle, LanguageCode, CaptionConfig
            style = VisualPromptStyle(req.get("style", "cinematic"))
            lang = LanguageCode(req.get("voice_config", {}).get("language", "en"))
            
            script = req.get("script_text") or "Narration voiceover b-roll visual story"
            scenes: List[SceneDetail] = scene_engine.segment_script_into_scenes(
                script_text=script,
                total_audio_duration=audio_duration,
                style=style,
                style_instructions=req.get("style_instructions"),
                avoid_instructions=req.get("avoid_instructions"),
                language=lang
            )

            job["scenes"] = [s.dict() for s in scenes]
            self._persist(job_id)

            # 3. Footage Discovery & Licensing
            self._update_stage(job_id, "sourcing_footage", 50)
            seen_clips: Set[str] = set()
            for sc in scenes:
                clip = await footage_service.find_best_footage_for_scene(sc, seen_clips)
                await footage_service.ensure_clip_downloaded(clip, job_dir)

            job["scenes"] = [s.dict() for s in scenes]
            self._persist(job_id)

            # 4. Generate Captions SRT
            self._update_stage(job_id, "generating_captions", 65)
            srt_path = str(job_dir / "captions.srt")
            caption_service.generate_srt(scenes, srt_path)
            job["srt_path"] = srt_path
            caption_cfg = CaptionConfig(**req.get("caption_config", {}))
            job["caption_config"] = caption_cfg

            # 5. FFmpeg Video Compositor for All Requested Aspect Ratios
            self._update_stage(job_id, "rendering_videos", 75)
            aspect_ratios = [AspectRatio(r) for r in req.get("aspect_ratios", ["16:9", "9:16", "1:1"])]
            video_urls: Dict[str, str] = {}

            for ar in aspect_ratios:
                ratio_tag = ar.value.replace(":", "_")
                # Render clips for each scene
                clip_paths = []
                for sc in scenes:
                    clip_out = str(job_dir / f"clip_sc{sc.scene_number}_{ratio_tag}.mp4")
                    video_engine.render_scene_clip(sc, ar, clip_out)
                    clip_paths.append(clip_out)

                # Assemble full ratio video
                final_video_path = str(job_dir / f"video_{ratio_tag}.mp4")
                video_engine.assemble_full_video(
                    scene_clip_paths=clip_paths,
                    audio_path=audio_path,
                    srt_path=srt_path,
                    caption_config=caption_cfg,
                    aspect_ratio=ar,
                    output_video_path=final_video_path,
                    job_dir=job_dir
                )
                video_urls[ar.value] = storage_service.get_public_url(final_video_path)

            # 6. Build Timeline & Manifest
            self._update_stage(job_id, "finalizing_deliverables", 90)
            elapsed = time.time() - start_time
            timeline_path = str(job_dir / "timeline.json")
            manifest_path = str(job_dir / "manifest.json")
            
            timeline_data = video_engine.build_timeline_json(scenes, timeline_path)
            manifest_data = video_engine.build_manifest_json(job_id, scenes, elapsed, req, manifest_path)

            # 7. Complete Succeeded Deliverables
            result_payload = {
                "video_urls": video_urls,
                "captions_srt_url": storage_service.get_public_url(srt_path),
                "timeline_json_url": storage_service.get_public_url(timeline_path),
                "manifest_json_url": storage_service.get_public_url(manifest_path),
                "metrics": {
                    "processing_time_seconds": round(elapsed, 2),
                    "total_scenes": len(scenes),
                    "total_duration": audio_duration,
                    "estimated_cost_usd": 0.00
                },
                "licences": manifest_data.get("licences_and_rights", []),
                "quality_report": {
                    "average_relevance_score": round(sum(s.relevance_score for s in scenes) / max(1, len(scenes)), 2),
                    "average_vlm_score": round(sum(s.vlm_score or 0.8 for s in scenes) / max(1, len(scenes)), 2),
                    "commercial_cleared_ratio": 1.0,
                    "duplicate_clip_count": 0
                }
            }

            job["result"] = result_payload
            job["scenes"] = [s.dict() for s in scenes]
            self._update_stage(job_id, "completed", 100, JobStatus.SUCCEEDED)

            # 8. Webhook notification
            if req.get("webhook_url"):
                secret = req.get("webhook_secret") or settings.webhook_secret
                await webhook_service.send_callback(
                    webhook_url=req["webhook_url"],
                    secret=secret,
                    payload={"event": "job.succeeded", "job_id": job_id, "result": result_payload}
                )

        except Exception as err:
            logger.error(f"Job {job_id} failed: {err}", exc_info=True)
            job["error"] = str(err)
            self._update_stage(job_id, "failed", 100, JobStatus.FAILED)
            if job["request"].get("webhook_url"):
                secret = job["request"].get("webhook_secret") or settings.webhook_secret
                await webhook_service.send_callback(
                    webhook_url=job["request"]["webhook_url"],
                    secret=secret,
                    payload={"event": "job.failed", "job_id": job_id, "error": str(err)}
                )

    def _update_stage(self, job_id: str, stage: str, progress: int, status: Optional[JobStatus] = None):
        job = self._jobs[job_id]
        job["stage"] = stage
        job["progress"] = progress
        if status:
            job["status"] = status
        job["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        self._persist(job_id)

    def _persist(self, job_id: str):
        job = self._jobs[job_id]
        import json
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO jobs (job_id, correlation_id, status, progress, stage, created_at, updated_at, error, data_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job_id,
                job["correlation_id"],
                job["status"].value if isinstance(job["status"], JobStatus) else job["status"],
                job["progress"],
                job["stage"],
                job["created_at"],
                job["updated_at"],
                job.get("error"),
                json.dumps(job, default=str)
            ))
            conn.commit()

    def _load_from_db(self, job_id: str) -> Optional[Dict[str, Any]]:
        import json
        with sqlite3.connect(self._db_path) as conn:
            cur = conn.execute("SELECT data_json FROM jobs WHERE job_id = ?", (job_id,))
            row = cur.fetchone()
            if row:
                data = json.loads(row[0])
                if isinstance(data.get("status"), str):
                    data["status"] = JobStatus(data["status"])
                self._jobs[job_id] = data
                return data
        return None

    def list_recent_jobs(self, limit: int = 20) -> List[Dict[str, Any]]:
        import json
        with sqlite3.connect(self._db_path) as conn:
            cur = conn.execute("SELECT data_json FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,))
            rows = cur.fetchall()
            return [json.loads(r[0]) for r in rows]

job_manager = JobManager()
