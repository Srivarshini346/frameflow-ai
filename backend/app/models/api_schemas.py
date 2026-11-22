from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, model_validator

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
    burn_in: bool = True
    srt: bool = True
    font_size: int = Field(default=32, ge=16, le=72)
    font_color: str = "#FFFFFF"
    background_box: bool = True
    subtitle_style: str = "highlight_current"

    @model_validator(mode="before")
    @classmethod
    def handle_aliases(cls, data: Any):
        if isinstance(data, dict):
            if "burned_in" in data and "burn_in" not in data:
                data["burn_in"] = data["burned_in"]
            if "enabled" in data and "srt" not in data:
                data["srt"] = data["enabled"]
        return data

class SceneInputRequest(BaseModel):
    text: str = ""
    visual_hint: Optional[str] = None
    manual_keywords: Optional[List[str]] = None

    @model_validator(mode="before")
    @classmethod
    def handle_aliases(cls, data: Any):
        if isinstance(data, dict):
            if "narration_text" in data and not data.get("text"):
                data["text"] = data["narration_text"]
            if "custom_visual_description" in data and not data.get("visual_hint"):
                data["visual_hint"] = data["custom_visual_description"]
        return data

class BrollJobCreateRequest(BaseModel):
    script: Optional[str] = None
    scenes: Optional[List[SceneInputRequest]] = None
    voice: VoiceConfig = Field(default_factory=VoiceConfig)
    aspect_ratios: List[AspectRatio] = Field(
        default=[AspectRatio.LANDSCAPE_16_9, AspectRatio.PORTRAIT_9_16, AspectRatio.SQUARE_1_1]
    )
    style: VisualPromptStyle = VisualPromptStyle.CINEMATIC
    avoid: List[str] = Field(default_factory=list)
    captions: CaptionConfig = Field(default_factory=CaptionConfig)
    audio_url: Optional[str] = None
    callback_url: Optional[str] = None
    webhook_secret: Optional[str] = None

    # Legacy & Multipart Aliases
    script_text: Optional[str] = None
    audio_base64: Optional[str] = None
    audio_filename: Optional[str] = None
    voice_config: Optional[VoiceConfig] = None
    style_instructions: Optional[str] = None
    avoid_instructions: Optional[List[str]] = None
    caption_config: Optional[CaptionConfig] = None
    webhook_url: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def map_aliases(cls, data: Any):
        if isinstance(data, dict):
            # Script
            if not data.get("script") and data.get("script_text"):
                data["script"] = data["script_text"]
            elif not data.get("script_text") and data.get("script"):
                data["script_text"] = data["script"]

            # Voice
            if not data.get("voice") and data.get("voice_config"):
                data["voice"] = data["voice_config"]
            elif not data.get("voice_config") and data.get("voice"):
                data["voice_config"] = data["voice"]

            # Avoid
            if not data.get("avoid") and data.get("avoid_instructions"):
                data["avoid"] = data["avoid_instructions"]
            elif not data.get("avoid_instructions") and data.get("avoid"):
                data["avoid_instructions"] = data["avoid"]

            # Captions
            if not data.get("captions") and data.get("caption_config"):
                data["captions"] = data["caption_config"]
            elif not data.get("caption_config") and data.get("captions"):
                data["caption_config"] = data["captions"]

            # Webhook
            if not data.get("callback_url") and data.get("webhook_url"):
                data["callback_url"] = data["webhook_url"]
            elif not data.get("webhook_url") and data.get("callback_url"):
                data["webhook_url"] = data["callback_url"]

        return data

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
    watermark: bool = False
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
    source: str = "mock"
    clip_id: str = ""
    source_url: str = ""
    licence: str = ""
    attribution: str = ""
    is_ai_generated: bool = False
    watermark: bool = False
    selection_rule: str = "CLIP image-text cosine similarity ranking"
    selection_reason: str = ""
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0)
    clip_rating: int = Field(default=3, ge=1, le=5)
    warnings: List[str] = Field(default_factory=list)
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

class JobResultResponse(BaseModel):
    job_id: str
    status: JobStatus
    video_urls: Dict[str, str] = Field(default_factory=dict)
    captions_srt_url: Optional[str] = None
    timeline_json_url: Optional[str] = None
    manifest_json_url: Optional[str] = None
    metrics: Dict[str, Any] = Field(default_factory=dict)
    licences: List[Dict[str, Any]] = Field(default_factory=list)
    quality_report: Dict[str, Any] = Field(default_factory=list)

class HealthStatus(BaseModel):
    status: str
    version: str
    ffmpeg_available: bool
    ffmpeg_version: Optional[str] = None
    storage_writable: bool
    database_connected: bool = True
    active_jobs: int = 0
