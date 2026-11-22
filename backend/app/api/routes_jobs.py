import uuid
import json
import base64
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, Header, Response, status, Request, UploadFile, File, Form
from app.models.api_schemas import (
    BrollJobCreateRequest, JobDetailResponse, JobResultResponse, SceneReplaceRequest,
    AspectRatio, VoiceConfig, VisualPromptStyle, CaptionConfig
)
from app.services.job_manager import job_manager
from app.core.idempotency import idempotency_store
from app.core.exceptions import ValidationError, EmptyScriptError, JobNotFoundError, IdempotencyKeyReusedError
from app.core.logger import logger

router = APIRouter(prefix="", tags=["B-roll Jobs"])

@router.post("/broll/jobs", status_code=status.HTTP_202_ACCEPTED, response_model=JobDetailResponse)
async def create_broll_job(
    request_data: BrollJobCreateRequest,
    response: Response,
    request: Request,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    x_correlation_id: Optional[str] = Header(None, alias="X-Correlation-ID")
):
    correlation_id = x_correlation_id or f"corr_{uuid.uuid4().hex[:12]}"

    # Check for empty script string
    has_script_field = request_data.script is not None or request_data.script_text is not None
    script_content = (request_data.script or request_data.script_text or "").strip()
    has_audio_url = bool(request_data.audio_url and request_data.audio_url.strip())
    has_audio_b64 = bool(request_data.audio_base64 and request_data.audio_base64.strip())
    has_scenes = bool(request_data.scenes and len(request_data.scenes) > 0)

    # If neither audio nor scenes are given, script must be non-empty
    if not (has_audio_url or has_audio_b64 or has_scenes):
        if not script_content:
            raise EmptyScriptError(
                "Script text is empty. Please provide a script, scenes, or an audio voiceover.",
                correlation_id=correlation_id
            )

    # Check idempotency
    payload_dict = request_data.dict()
    if idempotency_key:
        cached = idempotency_store.check_or_set(idempotency_key, payload_dict)
        if cached:
            logger.info(f"Returning idempotent cached response for key: {idempotency_key}")
            response.headers["X-Idempotency-Hit"] = "true"
            response.headers["X-Correlation-ID"] = correlation_id
            response.headers["Location"] = f"/api/v1/jobs/{cached['job_id']}"
            return cached

    job_id = f"job_{uuid.uuid4().hex[:10]}"
    job_detail = job_manager.create_job(request_data, correlation_id=correlation_id, job_id=job_id)

    response.headers["Location"] = f"/api/v1/jobs/{job_id}"
    response.headers["X-Correlation-ID"] = correlation_id

    # Cache response for idempotency
    if idempotency_key:
        idempotency_store.store_response(idempotency_key, payload_dict, job_detail.dict())

    return job_detail

@router.post("/broll/jobs/upload", status_code=status.HTTP_202_ACCEPTED, response_model=JobDetailResponse)
async def create_broll_job_with_audio_file(
    response: Response,
    audio_file: UploadFile = File(...),
    script: Optional[str] = Form(None),
    aspect_ratios: Optional[str] = Form(None),
    style: Optional[str] = Form("cinematic"),
    avoid: Optional[str] = Form(None),
    callback_url: Optional[str] = Form(None),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    x_correlation_id: Optional[str] = Header(None, alias="X-Correlation-ID")
):
    """
    Multipart audio file upload endpoint (MP3, WAV, M4A).
    """
    correlation_id = x_correlation_id or f"corr_{uuid.uuid4().hex[:12]}"
    content = await audio_file.read()
    b64_audio = base64.b64encode(content).decode("utf-8")

    ratios = [AspectRatio(r.strip()) for r in aspect_ratios.split(",")] if aspect_ratios else [
        AspectRatio.LANDSCAPE_16_9, AspectRatio.PORTRAIT_9_16, AspectRatio.SQUARE_1_1
    ]
    avoid_list = [a.strip() for a in avoid.split(",") if a.strip()] if avoid else []

    req = BrollJobCreateRequest(
        script=script,
        audio_base64=b64_audio,
        audio_filename=audio_file.filename,
        aspect_ratios=ratios,
        style=VisualPromptStyle(style or "cinematic"),
        avoid=avoid_list,
        callback_url=callback_url
    )

    if idempotency_key:
        cached = idempotency_store.check_or_set(idempotency_key, {"filename": audio_file.filename, "size": len(content)})
        if cached:
            response.headers["X-Idempotency-Hit"] = "true"
            response.headers["X-Correlation-ID"] = correlation_id
            return cached

    job_id = f"job_{uuid.uuid4().hex[:10]}"
    job_detail = job_manager.create_job(req, correlation_id=correlation_id, job_id=job_id)

    response.headers["Location"] = f"/api/v1/jobs/{job_id}"
    response.headers["X-Correlation-ID"] = correlation_id

    if idempotency_key:
        idempotency_store.store_response(idempotency_key, {"filename": audio_file.filename, "size": len(content)}, job_detail.dict())

    return job_detail

@router.get("/jobs/{job_id}", response_model=JobDetailResponse)
async def get_job_status(job_id: str, response: Response):
    job = job_manager.get_job_detail(job_id)
    response.headers["X-Correlation-ID"] = job.correlation_id
    return job

@router.get("/jobs/{job_id}/result", response_model=JobResultResponse)
async def get_job_result(job_id: str):
    return job_manager.get_job_result(job_id)

@router.post("/jobs/{job_id}/scenes/{scene_number}/replace", response_model=JobDetailResponse)
async def replace_scene_footage(
    job_id: str,
    scene_number: int,
    replace_req: SceneReplaceRequest
):
    """
    Incremental clip-level rerender: replaces footage of target scene
    and re-stitches videos without re-rendering unaffected scenes.
    """
    return await job_manager.replace_scene_footage(
        job_id=job_id,
        scene_number=scene_number,
        new_clip_id=replace_req.new_footage_id,
        custom_query=replace_req.custom_query
    )

@router.get("/jobs", response_model=List[JobDetailResponse])
async def list_recent_jobs(limit: int = 20):
    raw_jobs = job_manager.list_recent_jobs(limit=limit)
    out = []
    for r in raw_jobs:
        try:
            out.append(job_manager.get_job_detail(r["job_id"]))
        except Exception:
            pass
    return out

class JobRatingPayload(BaseModel):
    ratings: dict = Field(default_factory=dict)
    notes: Optional[str] = None
    overall_score: Optional[float] = None

@router.post("/jobs/{job_id}/rate")
async def rate_job_quality(job_id: str, payload: JobRatingPayload):
    """
    Saves human quality rating and feedback to /storage/ratings/<job_id>.json.
    """
    return job_manager.save_user_rating(
        job_id=job_id,
        ratings=payload.ratings,
        notes=payload.notes,
        overall_score=payload.overall_score
    )
