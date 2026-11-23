import os
import time
import base64
import asyncio
import sqlite3
from pathlib import Path
from typing import Dict, Any, List, Optional, Set

from app.models.api_schemas import (
    JobStatus, JobDetailResponse, JobResultResponse,
    BrollJobCreateRequest, SceneDetail, AspectRatio, FootageClip,
    VisualPromptStyle, LanguageCode, CaptionConfig, VoiceConfig
)
from app.services.audio_service import audio_service
from app.services.asr_service import get_asr_adapter, validate_audio_file
from app.services.scene_engine import scene_engine
from app.services.footage_service import footage_service
from app.services.video_engine import video_engine
from app.services.caption_service import caption_service
from app.services.storage_service import storage_service
from app.services.webhook_service import webhook_service
from app.services.video_validator import video_validator
from app.config import settings
from app.core.exceptions import FrameFlowError, JobNotFoundError, ValidationError, EmptyScriptError
from app.core.logger import logger

class JobManager:
    """
    Central background job orchestrator.
    Manages queued, running, succeeded, failed states, stage progress,
    scene timing, incremental clip rerendering, persistence, and deliverable validation.
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
        start_time = time.time()
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
        if target_scene.selected_footage:
            seen_clips.discard(target_scene.selected_footage.clip_id)

        avoid_list = job["request"].get("avoid") or job["request"].get("avoid_instructions") or []
        new_clip = await footage_service.find_best_footage_for_scene(target_scene, seen_clips, avoid_list=avoid_list)
        await footage_service.ensure_clip_downloaded(new_clip, job_dir)
        target_scene.selected_footage = new_clip
        thumb_file = job_dir / f"thumb_scene_{scene_number}.jpg"
        if video_engine.extract_scene_thumbnail(new_clip.local_path, str(thumb_file)):
            target_scene.thumbnail_url = f"/storage/jobs/{job_id}/thumb_scene_{scene_number}.jpg"
        scenes[target_scene_idx] = target_scene.dict()

        aspect_ratios = [AspectRatio(r) for r in job["request"].get("aspect_ratios", ["16:9", "9:16", "1:1"])]
        audio_path = job["audio_path"]
        srt_path = job["srt_path"]
        caption_cfg = CaptionConfig(**job["request"].get("captions", job["request"].get("caption_config", {})))

        validation_reports: Dict[str, Any] = {}
        for ar in aspect_ratios:
            ratio_tag = ar.value.replace(":", "_")
            clip_path = str(job_dir / f"clip_sc{scene_number}_{ratio_tag}.mp4")
            video_engine.render_scene_clip(target_scene, ar, clip_path)

            all_clip_paths = [
                str(job_dir / f"clip_sc{s['scene_number']}_{ratio_tag}.mp4") for s in scenes
            ]
            final_out = str(job_dir / f"video_{ratio_tag}.mp4")
            video_engine.assemble_full_video(
                all_clip_paths, audio_path, srt_path, caption_cfg, ar, final_out, job_dir
            )
            val = video_validator.validate_video(final_out, expected_ar=ar.value)
            validation_reports[ar.value] = val.to_dict()

        scene_objs = [SceneDetail(**s) for s in scenes]
        timeline_path = str(job_dir / "timeline.json")
        manifest_path = str(job_dir / "manifest.json")
        video_engine.build_timeline_json(scene_objs, timeline_path)
        video_engine.build_manifest_json(
            job_id, scene_objs, time.time() - start_time, job["request"], validation_reports, manifest_path
        )

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
        stage_timings: Dict[str, float] = {}

        try:
            t0 = time.time()
            self._update_stage(job_id, "validating", 5, JobStatus.RUNNING)
            req = job["request"]
            stage_timings["validating"] = round(time.time() - t0, 3)

            # 1. Audio and narration processing
            t1 = time.time()
            audio_path = str(job_dir / "narration.wav")
            audio_duration = 5.0
            script_text = req.get("script") or req.get("script_text")

            if req.get("audio_base64"):
                self._update_stage(job_id, "transcribing_narration", 15)
                raw_bytes = base64.b64decode(req["audio_base64"])
                raw_audio_path = str(job_dir / (req.get("audio_filename") or "uploaded_audio.wav"))
                with open(raw_audio_path, "wb") as f:
                    f.write(raw_bytes)
                audio_props = validate_audio_file(raw_audio_path)
                audio_path = raw_audio_path
                audio_duration = audio_props["duration"]

                # Run ASR adapter to transcribe narration
                asr = get_asr_adapter()
                asr_result = asr.transcribe(audio_path)
                if not script_text:
                    script_text = asr_result.text
            elif req.get("audio_url"):
                self._update_stage(job_id, "fetching_audio", 15)
                import httpx
                async with httpx.AsyncClient(timeout=20.0) as client:
                    res = await client.get(req["audio_url"])
                    raw_audio_path = str(job_dir / "remote_audio.wav")
                    with open(raw_audio_path, "wb") as f:
                        f.write(res.content)
                audio_props = validate_audio_file(raw_audio_path)
                audio_path = raw_audio_path
                audio_duration = audio_props["duration"]

                asr = get_asr_adapter()
                asr_result = asr.transcribe(audio_path)
                if not script_text:
                    script_text = asr_result.text
            else:
                self._update_stage(job_id, "synthesizing_speech", 15)
                if not script_text or not script_text.strip():
                    raise EmptyScriptError("Either script, scenes, audio_url, or audio upload must be provided")

                voice_dict = req.get("voice") or req.get("voice_config") or {}
                voice_cfg = VoiceConfig(**voice_dict)
                tts_res = await audio_service.generate_speech(script_text, voice_cfg, audio_path)
                audio_duration = tts_res["duration"]

            job["audio_path"] = audio_path
            job["audio_duration"] = audio_duration
            stage_timings["audio_processing"] = round(time.time() - t1, 3)

            # 2. Intelligent Scene Segmentation
            t2 = time.time()
            self._update_stage(job_id, "segmenting_scenes", 30)
            style_val = req.get("style") or "cinematic"
            style = VisualPromptStyle(style_val if isinstance(style_val, str) else style_val.value)
            
            voice_dict = req.get("voice") or req.get("voice_config") or {}
            lang_code = voice_dict.get("language", "en")
            lang = LanguageCode(lang_code.value if hasattr(lang_code, "value") else lang_code)
            
            avoid_list = req.get("avoid") or req.get("avoid_instructions") or []
            
            scenes: List[SceneDetail] = scene_engine.segment_script_into_scenes(
                script_text=script_text or "Narration voiceover b-roll visual story",
                total_audio_duration=audio_duration,
                style=style,
                style_instructions=req.get("style_instructions"),
                avoid_instructions=avoid_list,
                language=lang
            )

            job["scenes"] = [s.dict() for s in scenes]
            self._persist(job_id)
            stage_timings["scene_segmentation"] = round(time.time() - t2, 3)

            # 3. Footage Discovery & Licensing (Concurrent Download Pool)
            t3 = time.time()
            self._update_stage(job_id, "sourcing_footage", 40)
            seen_clips: Set[str] = set()
            ratios_raw = req.get("aspect_ratios", ["16:9"])
            primary_ratio = str(ratios_raw[0].value if hasattr(ratios_raw[0], "value") else ratios_raw[0]) if ratios_raw else "16:9"

            # 3A. Select best footage for each scene
            for sc in scenes:
                clip = await footage_service.find_best_footage_for_scene(
                    sc, seen_clips, avoid_list=avoid_list, aspect_ratio=primary_ratio
                )
                seen_clips.add(clip.clip_id)

            # 3B. Concurrent download & thumbnail generation (up to 6 parallel workers)
            dl_sem = asyncio.Semaphore(6)
            total_sc = len(scenes)
            dl_count = 0

            async def _download_and_thumb(sc: SceneDetail):
                nonlocal dl_count
                async with dl_sem:
                    local_path = await footage_service.ensure_clip_downloaded(sc.selected_footage, job_dir)
                    thumb_file = job_dir / f"thumb_scene_{sc.scene_number}.jpg"
                    if await asyncio.to_thread(video_engine.extract_scene_thumbnail, local_path, str(thumb_file)):
                        sc.thumbnail_url = f"/storage/jobs/{job_id}/thumb_scene_{sc.scene_number}.jpg"
                    dl_count += 1
                    pct = min(64, int(40 + (dl_count / max(1, total_sc)) * 24))
                    self._update_stage(job_id, f"sourcing_footage ({dl_count}/{total_sc})", pct)

            await asyncio.gather(*[_download_and_thumb(sc) for sc in scenes])

            job["scenes"] = [s.dict() for s in scenes]
            self._persist(job_id)
            stage_timings["footage_discovery"] = round(time.time() - t3, 3)

            # 4. Generate Captions SRT
            t4 = time.time()
            self._update_stage(job_id, "generating_captions", 65)
            srt_path = str(job_dir / "captions.srt")
            caption_service.generate_srt(scenes, srt_path)
            job["srt_path"] = srt_path
            cap_dict = req.get("captions") or req.get("caption_config") or {}
            caption_cfg = CaptionConfig(**cap_dict)
            job["caption_config"] = caption_cfg
            stage_timings["caption_generation"] = round(time.time() - t4, 3)

            # 5. FFmpeg Video Compositor for All Requested Aspect Ratios (Parallel 4-Worker Pool)
            t5 = time.time()
            self._update_stage(job_id, "rendering_videos", 70)
            await asyncio.sleep(0.01)

            ratios_raw = req.get("aspect_ratios", ["16:9"])
            aspect_ratios = [AspectRatio(r.value if hasattr(r, "value") else r) for r in ratios_raw]
            video_urls: Dict[str, str] = {}
            validation_reports: Dict[str, Any] = {}

            total_items = max(1, len(aspect_ratios) * len(scenes) + len(aspect_ratios))
            completed_items = 0
            render_sem = asyncio.Semaphore(4)

            for ar in aspect_ratios:
                ratio_tag = ar.value.replace(":", "_")
                
                async def _render_clip(sc: SceneDetail):
                    nonlocal completed_items
                    clip_out = str(job_dir / f"clip_sc{sc.scene_number}_{ratio_tag}.mp4")
                    async with render_sem:
                        await asyncio.to_thread(video_engine.render_scene_clip, sc, ar, clip_out)
                    completed_items += 1
                    pct = min(92, int(70 + (completed_items / total_items) * 22))
                    self._update_stage(
                        job_id,
                        f"rendering_videos ({completed_items}/{len(scenes)} {ar.value})",
                        pct
                    )
                    return (sc.scene_number, clip_out)

                tasks = [_render_clip(sc) for sc in scenes]
                clip_results = await asyncio.gather(*tasks)
                clip_results.sort(key=lambda x: x[0])
                clip_paths = [r[1] for r in clip_results]

                # Assemble full ratio video
                self._update_stage(job_id, f"assembling_video ({ar.value})", min(94, pct + 2))
                await asyncio.sleep(0.01)

                final_video_path = str(job_dir / f"video_{ratio_tag}.mp4")
                await asyncio.to_thread(
                    video_engine.assemble_full_video,
                    scene_clip_paths=clip_paths,
                    audio_path=audio_path,
                    srt_path=srt_path,
                    caption_config=caption_cfg,
                    aspect_ratio=ar,
                    output_video_path=final_video_path,
                    job_dir=job_dir
                )

                completed_items += 1
                # Post-render FFprobe automated quality validation
                val = await asyncio.to_thread(video_validator.validate_video, final_video_path, expected_ar=ar.value)
                validation_reports[ar.value] = val.to_dict()

                # Upload to MinIO/S3 or Local Storage
                video_urls[ar.value] = storage_service.upload_file(final_video_path)

            stage_timings["video_rendering"] = round(time.time() - t5, 3)

            # 6. Build Timeline & Manifest
            t6 = time.time()
            self._update_stage(job_id, "finalizing_deliverables", 90)
            elapsed = time.time() - start_time
            timeline_path = str(job_dir / "timeline.json")
            manifest_path = str(job_dir / "manifest.json")
            
            timeline_data = video_engine.build_timeline_json(scenes, timeline_path)
            manifest_data = video_engine.build_manifest_json(
                job_id=job_id,
                scenes=scenes,
                processing_time_s=elapsed,
                request_params=req,
                validation_reports=validation_reports,
                output_path=manifest_path,
                seed=42,
                stage_timings=stage_timings
            )

            # Upload metadata deliverables
            srt_url = storage_service.upload_file(srt_path)
            timeline_url = storage_service.upload_file(timeline_path)
            manifest_url = storage_service.upload_file(manifest_path)
            stage_timings["finalizing_deliverables"] = round(time.time() - t6, 3)

            # 7. Complete Succeeded Deliverables
            result_payload = {
                "video_urls": video_urls,
                "captions_srt_url": srt_url,
                "timeline_json_url": timeline_url,
                "manifest_json_url": manifest_url,
                "metrics": {
                    "processing_time_seconds": round(elapsed, 2),
                    "total_scenes": len(scenes),
                    "total_duration": audio_duration,
                    "estimated_cost_usd": manifest_data.get("estimated_cost_usd", 0.00),
                    "stage_timings": stage_timings
                },
                "licences": manifest_data.get("licences_and_rights", []),
                "quality_report": {
                    "average_relevance_score": round(sum(s.relevance_score for s in scenes) / max(1, len(scenes)), 2),
                    "commercial_cleared_ratio": 1.0,
                    "duplicate_clip_count": 0,
                    "validation": validation_reports
                }
            }

            job["result"] = result_payload
            job["scenes"] = [s.dict() for s in scenes]
            self._update_stage(job_id, "completed", 100, JobStatus.SUCCEEDED)

            # 8. Webhook notification
            callback_target = req.get("callback_url") or req.get("webhook_url")
            if callback_target:
                secret = req.get("webhook_secret") or settings.webhook_secret
                await webhook_service.send_callback(
                    webhook_url=callback_target,
                    secret=secret,
                    payload={"event": "job.succeeded", "job_id": job_id, "result": result_payload}
                )

        except Exception as err:
            logger.error(f"Job {job_id} failed: {err}", exc_info=True)
            job["error"] = str(err)
            self._update_stage(job_id, "failed", 100, JobStatus.FAILED)
            callback_target = job["request"].get("callback_url") or job["request"].get("webhook_url")
            if callback_target:
                secret = job["request"].get("webhook_secret") or settings.webhook_secret
                await webhook_service.send_callback(
                    webhook_url=callback_target,
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

    def cleanup_orphaned_jobs_on_startup(self):
        """
        Marks any queued or running jobs from a previous server process as failed,
        preventing infinite loading spinners in the history and workspace views.
        """
        try:
            with sqlite3.connect(self._db_path) as conn:
                conn.execute("""
                    UPDATE jobs
                    SET status = 'failed',
                        stage = 'interrupted',
                        error = 'Interrupted by server restart',
                        updated_at = datetime('now')
                    WHERE status IN ('running', 'queued')
                """)
                conn.commit()
            logger.info("Checked and recovered orphaned running/queued jobs on startup.")
        except Exception as e:
            logger.warning(f"Error recovering orphaned jobs on startup: {e}")

    def save_user_rating(
        self,
        job_id: str,
        ratings: Dict[str, Any],
        notes: Optional[str] = None,
        overall_score: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Persists human-in-the-loop quality evaluation ratings and notes to storage.
        """
        import json
        ratings_dir = settings.storage_dir / "ratings"
        ratings_dir.mkdir(parents=True, exist_ok=True)
        rating_file = ratings_dir / f"{job_id}.json"

        rating_data = {
            "job_id": job_id,
            "ratings": ratings,
            "notes": notes or "",
            "overall_score": overall_score,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        with open(rating_file, "w", encoding="utf-8") as f:
            json.dump(rating_data, f, indent=2)

        job = self._jobs.get(job_id) or self._load_from_db(job_id)
        if job and job.get("result"):
            if "quality_report" in job["result"]:
                job["result"]["quality_report"]["human_ratings"] = rating_data
                self._persist(job_id)

        logger.info(f"Saved human rating for job {job_id} to {rating_file}")
        return rating_data

job_manager = JobManager()
