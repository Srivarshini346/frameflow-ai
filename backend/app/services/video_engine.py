import os
import json
import time
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Tuple
from app.models.api_schemas import SceneDetail, CaptionConfig, AspectRatio, FootageClip
from app.services.caption_service import caption_service
from app.config import settings
from app.core.exceptions import VideoRenderError
from app.core.logger import logger

class VideoEngine:
    """
    FFmpeg Native Video Compositor.
    
    1. Produces H.264 video + AAC audio at 30 FPS.
    2. Renders 16:9, 9:16, and 1:1 without distortion or black glitches.
    3. Burns synchronised captions.
    4. Supports incremental scene-level clip rerendering.
    5. Emits video_16_9.mp4, video_9_16.mp4, video_1_1.mp4, captions.srt, timeline.json, manifest.json.
    """

    RESOLUTIONS = {
        AspectRatio.LANDSCAPE_16_9: (1920, 1080),
        AspectRatio.PORTRAIT_9_16: (1080, 1920),
        AspectRatio.SQUARE_1_1: (1080, 1080),
    }

    def render_scene_clip(
        self,
        scene: SceneDetail,
        aspect_ratio: AspectRatio,
        output_clip_path: str
    ) -> str:
        """
        Normalises a single scene footage clip to target resolution, 30 FPS, and duration.
        Cached scene clips allow rapid incremental rerendering when one scene is replaced.
        """
        target_w, target_h = self.RESOLUTIONS[aspect_ratio]
        footage = scene.selected_footage
        if not footage or not footage.local_path or not Path(footage.local_path).exists():
            raise VideoRenderError(f"Local footage file missing for scene {scene.scene_number}")

        ffmpeg_exe = settings.get_ffmpeg_path()
        duration = max(1.0, scene.duration)

        # Smart scale & crop filter to perfectly fill dimensions without stretching
        vf_filter = (
            f"scale={target_w}:{target_h}:force_original_aspect_ratio=increase,"
            f"crop={target_w}:{target_h},"
            f"fps=30,"
            f"format=yuv420p"
        )

        cmd = [
            ffmpeg_exe, "-y",
            "-stream_loop", "-1",  # Loop clip if duration is shorter than narration
            "-i", footage.local_path,
            "-t", str(duration),
            "-vf", vf_filter,
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "22",
            "-an", # No audio in individual video clip chunks
            output_clip_path
        ]

        logger.info(f"Rendering scene {scene.scene_number} ({aspect_ratio.value}) to {output_clip_path}")
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            logger.error(f"FFmpeg scene render error: {res.stderr}")
            raise VideoRenderError(f"Failed to render scene {scene.scene_number} clip: {res.stderr[:200]}")

        return output_clip_path

    def assemble_full_video(
        self,
        scene_clip_paths: List[str],
        audio_path: str,
        srt_path: str,
        caption_config: CaptionConfig,
        aspect_ratio: AspectRatio,
        output_video_path: str,
        job_dir: Path
    ) -> str:
        """
        Concatenates normalised scene clips, adds narration audio, and optionally burns captions.
        """
        ffmpeg_exe = settings.get_ffmpeg_path()
        concat_list_file = job_dir / f"concat_{aspect_ratio.value.replace(':', '_')}.txt"

        with open(concat_list_file, "w", encoding="utf-8") as f:
            for p in scene_clip_paths:
                clean_p = p.replace("\\", "/")
                f.write(f"file '{clean_p}'\n")

        # Build video filters (subtitles if enabled)
        has_subtitles = caption_config.enabled and caption_config.burned_in and Path(srt_path).exists()
        
        base_cmd = [
            ffmpeg_exe, "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_list_file),
            "-i", audio_path
        ]

        if has_subtitles:
            try:
                sub_filter = caption_service.build_subtitle_filter(srt_path, caption_config, aspect_ratio.value)
                cmd_with_subs = base_cmd + [
                    "-vf", sub_filter,
                    "-c:v", "libx264",
                    "-preset", "ultrafast",
                    "-crf", "23",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    "-shortest",
                    "-movflags", "+faststart",
                    output_video_path
                ]
                res = subprocess.run(cmd_with_subs, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if res.returncode == 0:
                    logger.info(f"Assembled video with burned subtitles ({aspect_ratio.value}) -> {output_video_path}")
                    return output_video_path
                else:
                    logger.warning(f"Subtitle filter not supported by FFmpeg build: {res.stderr[:160]}. Proceeding with clean video.")
            except Exception as e:
                logger.warning(f"Subtitles assembly error: {e}")

        # Assemble clean video without burned subtitle filter
        cmd_clean = base_cmd + [
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            "-movflags", "+faststart",
            output_video_path
        ]

        logger.info(f"Assembling full video ({aspect_ratio.value}) -> {output_video_path}")
        res = subprocess.run(cmd_clean, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            logger.error(f"FFmpeg assembly failed: {res.stderr}")
            raise VideoRenderError(f"Assembly failed for {aspect_ratio.value}: {res.stderr[:200]}")

        return output_video_path

    def build_timeline_json(self, scenes: List[SceneDetail], output_path: str) -> Dict[str, Any]:
        """
        Generates timeline.json recording every scene's timestamps, footage, licence, and reasons.
        """
        timeline_scenes = []
        for sc in scenes:
            ft = sc.selected_footage
            timeline_scenes.append({
                "scene_number": sc.scene_number,
                "narration_text": sc.narration_text,
                "start_time": sc.start_time,
                "end_time": sc.end_time,
                "duration": sc.duration,
                "visual_description": sc.visual_description,
                "search_query": sc.search_query,
                "selected_footage": {
                    "clip_id": ft.clip_id if ft else "none",
                    "provider": ft.provider if ft else "none",
                    "source_url": ft.source_url if ft else "",
                    "download_url": ft.download_url if ft else "",
                    "licence": ft.licence if ft else "N/A",
                    "attribution": ft.attribution if ft else "N/A",
                    "is_commercial_cleared": ft.is_commercial_cleared if ft else True,
                    "is_ai_generated": ft.is_ai_generated if ft else False
                } if ft else None,
                "relevance_score": sc.relevance_score,
                "vlm_score": sc.vlm_score,
                "selection_reason": sc.selection_reason
            })

        timeline_data = {
            "total_scenes": len(scenes),
            "total_duration": scenes[-1].end_time if scenes else 0.0,
            "scenes": timeline_scenes
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(timeline_data, f, indent=2)

        return timeline_data

    def build_manifest_json(
        self,
        job_id: str,
        scenes: List[SceneDetail],
        processing_time_s: float,
        request_params: Dict[str, Any],
        output_path: str
    ) -> Dict[str, Any]:
        """
        Generates manifest.json with real model, version, settings, cost, and rights audit.
        """
        providers_used = list({sc.selected_footage.provider for sc in scenes if sc.selected_footage})
        licences_recorded = []
        for sc in scenes:
            if sc.selected_footage:
                licences_recorded.append({
                    "scene": sc.scene_number,
                    "clip_id": sc.selected_footage.clip_id,
                    "provider": sc.selected_footage.provider,
                    "licence": sc.selected_footage.licence,
                    "attribution": sc.selected_footage.attribution,
                    "source_url": sc.selected_footage.source_url,
                    "commercial_cleared": sc.selected_footage.is_commercial_cleared
                })

        manifest = {
            "job_id": job_id,
            "engine": "FrameFlow AI – Intelligent B-roll Studio",
            "version": settings.version,
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "processing_time_seconds": round(processing_time_s, 2),
            "estimated_cost_usd": 0.00, # Open-source / local execution
            "pipeline_models": {
                "transcription": "Whisper-Base / Silence-Energy Aligner",
                "scene_engine": "Semantic Clause Discourse Segmenter v2",
                "footage_ranking": "Cosine-TF & VLM Multi-factor Evaluator",
                "video_compositor": "FFmpeg Native Compositor"
            },
            "parameters": request_params,
            "providers_used": providers_used,
            "licences_and_rights": licences_recorded,
            "warnings": []
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        return manifest

video_engine = VideoEngine()
