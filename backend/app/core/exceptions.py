from typing import Any, Optional
from fastapi import status
from fastapi.responses import JSONResponse

class FrameFlowError(Exception):
    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_SERVER_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        retryable: bool = False,
        details: Optional[Any] = None,
        correlation_id: Optional[str] = None
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.retryable = retryable
        self.details = details
        self.correlation_id = correlation_id

    def to_dict(self) -> dict:
        err = {
            "code": self.code,
            "message": self.message,
            "retryable": self.retryable,
            "details": self.details if self.details is not None else {}
        }
        if self.correlation_id:
            err["correlation_id"] = self.correlation_id
        return {"error": err}

    def to_response(self) -> JSONResponse:
        return JSONResponse(status_code=self.status_code, content=self.to_dict())

class ValidationError(FrameFlowError):
    def __init__(self, message: str, details: Optional[Any] = None, correlation_id: Optional[str] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=status.HTTP_400_BAD_REQUEST,
            retryable=False,
            details=details,
            correlation_id=correlation_id
        )

class WrongAudioFormatError(FrameFlowError):
    def __init__(self, message: str = "Unsupported audio format. Allowed: .mp3, .wav, .m4a", details: Optional[Any] = None, correlation_id: Optional[str] = None):
        super().__init__(
            message=message,
            code="WRONG_AUDIO_FORMAT",
            status_code=status.HTTP_400_BAD_REQUEST,
            retryable=False,
            details=details,
            correlation_id=correlation_id
        )

class EmptyAudioError(FrameFlowError):
    def __init__(self, message: str = "Uploaded audio is empty or corrupt", details: Optional[Any] = None, correlation_id: Optional[str] = None):
        super().__init__(
            message=message,
            code="EMPTY_AUDIO",
            status_code=status.HTTP_400_BAD_REQUEST,
            retryable=False,
            details=details,
            correlation_id=correlation_id
        )

class AudioTooLongError(FrameFlowError):
    def __init__(self, message: str = "Audio duration exceeds 10 minute limit", details: Optional[Any] = None, correlation_id: Optional[str] = None):
        super().__init__(
            message=message,
            code="AUDIO_TOO_LONG",
            status_code=status.HTTP_400_BAD_REQUEST,
            retryable=False,
            details=details,
            correlation_id=correlation_id
        )

class SilentAudioError(FrameFlowError):
    def __init__(self, message: str = "Audio is completely silent. Please provide audible narration.", details: Optional[Any] = None, correlation_id: Optional[str] = None):
        super().__init__(
            message=message,
            code="SILENT_AUDIO",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            retryable=False,
            details=details,
            correlation_id=correlation_id
        )

class MusicOnlyAudioError(FrameFlowError):
    def __init__(self, message: str = "Audio contains music/noise with no detectable spoken voiceover.", details: Optional[Any] = None, correlation_id: Optional[str] = None):
        super().__init__(
            message=message,
            code="MUSIC_ONLY_AUDIO",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            retryable=False,
            details=details,
            correlation_id=correlation_id
        )

class EmptyScriptError(FrameFlowError):
    def __init__(self, message: str = "Script text is empty", details: Optional[Any] = None, correlation_id: Optional[str] = None):
        super().__init__(
            message=message,
            code="EMPTY_SCRIPT",
            status_code=status.HTTP_400_BAD_REQUEST,
            retryable=False,
            details=details,
            correlation_id=correlation_id
        )

class JobNotFoundError(FrameFlowError):
    def __init__(self, job_id: str, correlation_id: Optional[str] = None):
        super().__init__(
            message=f"Job with ID '{job_id}' not found",
            code="JOB_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            retryable=False,
            details={"job_id": job_id},
            correlation_id=correlation_id
        )

class IdempotencyKeyReusedError(FrameFlowError):
    def __init__(self, key: str, correlation_id: Optional[str] = None):
        super().__init__(
            message=f"Idempotency key '{key}' was previously used with a different request payload",
            code="IDEMPOTENCY_KEY_REUSED",
            status_code=status.HTTP_409_CONFLICT,
            retryable=False,
            details={"idempotency_key": key},
            correlation_id=correlation_id
        )

class ProviderTimeoutError(FrameFlowError):
    def __init__(self, provider: str, details: Optional[Any] = None, correlation_id: Optional[str] = None):
        super().__init__(
            message=f"Footage provider '{provider}' timed out while searching for clips",
            code="PROVIDER_TIMEOUT",
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            retryable=True,
            details=details,
            correlation_id=correlation_id
        )

class FootageSearchError(FrameFlowError):
    def __init__(self, message: str, details: Optional[Any] = None, correlation_id: Optional[str] = None):
        super().__init__(
            message=message,
            code="FOOTAGE_SEARCH_ERROR",
            status_code=status.HTTP_502_BAD_GATEWAY,
            retryable=True,
            details=details,
            correlation_id=correlation_id
        )

class VideoRenderError(FrameFlowError):
    def __init__(self, message: str, details: Optional[Any] = None, correlation_id: Optional[str] = None):
        super().__init__(
            message=message,
            code="VIDEO_RENDER_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            retryable=True,
            details=details,
            correlation_id=correlation_id
        )
