from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"

class AspectRatio(str, Enum):
    LANDSCAPE_16_9 = "16:9"
    PORTRAIT_9_16 = "9:16"
    SQUARE_1_1 = "1:1"

class VisualPromptStyle(str, Enum):
    REALISTIC = "realistic"
    CINEMATIC = "cinematic"
    MINIMALIST = "minimalist"
    DYNAMIC = "dynamic"
    DOCUMENTARY = "documentary"

class LanguageCode(str, Enum):
    EN = "en"
    HI = "hi"
    TA = "ta"

class VoiceConfig(BaseModel):
    language: LanguageCode = LanguageCode.EN
    voice_name: str = "default"
    speech_rate: float = Field(default=1.0, ge=0.5, le=2.0)
    pitch: float = Field(default=0.0, ge=-10.0, le=10.0)

class CaptionConfig(BaseModel):
    enabled: bool = True
    burned_in: bool = True
    font_size: int = Field(default=32, ge=16, le=72)
    font_color: str = "#FFFFFF"
    background_box: bool = True
    subtitle_style: str = "highlight_current"

class SceneInputRequest(BaseModel):
    narration_text: str
    custom_visual_description: Optional[str] = None
    manual_keywords: Optional[List[str]] = None

class BrollJobCreateRequest(BaseModel):
    script_text: Optional[str] = Field(default=None, description="Plain text narration script")
    audio_url: Optional[str] = Field(default=None, description="Direct URL to pre-recorded audio file")
    audio_base64: Optional[str] = Field(default=None, description="Base64-encoded audio bytes (MP3, WAV, M4A)")
    audio_filename: Optional[str] = None
    scenes: Optional[List[SceneInputRequest]] = Field(default=None, description="Explicit manual scenes if not auto-segmenting")
    voice_config: VoiceConfig = Field(default_factory=VoiceConfig)
    aspect_ratios: List[AspectRatio] = Field(
        default=[AspectRatio.LANDSCAPE_16_9, AspectRatio.PORTRAIT_9_16, AspectRatio.SQUARE_1_1]
    )
    style: VisualPromptStyle = VisualPromptStyle.CINEMATIC
    style_instructions: Optional[str] = Field(default=None, description="Global visual mood directions")
    avoid_instructions: Optional[List[str]] = Field(default=None, description="Visual keywords/concepts to avoid")
    caption_config: CaptionConfig = Field(default_factory=CaptionConfig)
    webhook_url: Optional[str] = None
    webhook_secret: Optional[str] = None

class FootageClip(BaseModel):
    clip_id: str
    provider: str
    source_url: str
    download_url: str
    local_path: Optional[str] = None
    width: int
    height: int
    duration: float
    fps: float = 30.0
    licence: str
    attribution: str
    is_commercial_cleared: bool = True
    is_ai_generated: bool = False
    tags: List[str] = []

class SceneDetail(BaseModel):
    scene_number: int
    narration_text: str
    start_time: float
    end_time: float
    duration: float
    visual_description: str
    search_query: str
    selected_footage: Optional[FootageClip] = None
    ai_generated: bool = False
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0)
    vlm_score: Optional[float] = None
    selection_reason: str = ""
    status: str = "ready"

class SceneReplaceRequest(BaseModel):
    new_footage_id: Optional[str] = None
    custom_query: Optional[str] = None
    new_visual_description: Optional[str] = None

class JobDetailResponse(BaseModel):
    job_id: str
    correlation_id: str
    status: JobStatus
    progress: int = Field(ge=0, le=100)
    stage: str
    scenes: List[SceneDetail] = []
    warnings: List[str] = []
    error: Optional[str] = None
    created_at: str
    updated_at: str

class VideoUrlMap(BaseModel):
    ratio_16_9: Optional[str] = Field(default=None, alias="16:9")
    ratio_9_16: Optional[str] = Field(default=None, alias="9:16")
    ratio_1_1: Optional[str] = Field(default=None, alias="1:1")

    class Config:
        populate_by_name = True

class JobResultResponse(BaseModel):
    job_id: str
    status: JobStatus
    video_urls: Dict[str, str] = Field(default_factory=dict)
    captions_srt_url: Optional[str] = None
    timeline_json_url: Optional[str] = None
    manifest_json_url: Optional[str] = None
    metrics: Dict[str, Any] = Field(default_factory=dict)
    licences: List[Dict[str, Any]] = Field(default_factory=list)
    quality_report: Dict[str, Any] = Field(default_factory=dict)

class HealthStatus(BaseModel):
    status: str
    version: str
    ffmpeg_available: bool
    ffmpeg_version: Optional[str] = None
    storage_writable: bool
    active_jobs: int
