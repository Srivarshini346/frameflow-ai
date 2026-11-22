import uuid
from typing import Optional, List
from fastapi import APIRouter, Header, Response, status, Request
from app.models.api_schemas import (
    BrollJobCreateRequest, JobDetailResponse, JobResultResponse, SceneReplaceRequest
)
from app.services.job_manager import job_manager
from app.core.idempotency import idempotency_store
from app.core.exceptions import ValidationError, JobNotFoundError
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

    # Validate input: must have either script_text, audio_url, or audio_base64
    has_script = bool(request_data.script_text and request_data.script_text.strip())
    has_audio_url = bool(request_data.audio_url and request_data.audio_url.strip())
    has_audio_b64 = bool(request_data.audio_base64 and request_data.audio_base64.strip())

    if not (has_script or has_audio_url or has_audio_b64):
        raise ValidationError(
            "At least one narration input (script_text, audio_url, or audio_base64) is required",
            correlation_id=correlation_id
        )

    # Idempotency check
    if idempotency_key:
        cached = idempotency_store.get(idempotency_key)
        if cached:
            logger.info(f"Returning idempotent response for key: {idempotency_key}")
            response.headers["X-Idempotency-Hit"] = "true"
            response.headers["X-Correlation-ID"] = correlation_id
            return cached

    job_id = f"job_{uuid.uuid4().hex[:10]}"
    job_detail = job_manager.create_job(request_data, correlation_id=correlation_id, job_id=job_id)

    response.headers["Location"] = f"/api/v1/jobs/{job_id}"
    response.headers["X-Correlation-ID"] = correlation_id

    # Cache for idempotency
    if idempotency_key:
        idempotency_store.set(idempotency_key, job_detail.dict())

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
