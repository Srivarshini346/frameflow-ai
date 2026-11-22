from typing import Any, Optional
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse

class FrameFlowError(Exception):
    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Any] = None,
        correlation_id: Optional[str] = None
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details
        self.correlation_id = correlation_id

    def to_dict(self) -> dict:
        err = {
            "code": self.code,
            "message": self.message,
        }
        if self.details is not None:
            err["details"] = self.details
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
            details=details,
            correlation_id=correlation_id
        )

class AudioProcessingError(FrameFlowError):
    def __init__(self, message: str, details: Optional[Any] = None, correlation_id: Optional[str] = None):
        super().__init__(
            message=message,
            code="AUDIO_PROCESSING_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
            correlation_id=correlation_id
        )

class FootageSearchError(FrameFlowError):
    def __init__(self, message: str, details: Optional[Any] = None, correlation_id: Optional[str] = None):
        super().__init__(
            message=message,
            code="FOOTAGE_SEARCH_ERROR",
            status_code=status.HTTP_502_BAD_GATEWAY,
            details=details,
            correlation_id=correlation_id
        )

class VideoRenderError(FrameFlowError):
    def __init__(self, message: str, details: Optional[Any] = None, correlation_id: Optional[str] = None):
        super().__init__(
            message=message,
            code="VIDEO_RENDER_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
            correlation_id=correlation_id
        )

class JobNotFoundError(FrameFlowError):
    def __init__(self, job_id: str, correlation_id: Optional[str] = None):
        super().__init__(
            message=f"Job with ID '{job_id}' not found",
            code="JOB_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"job_id": job_id},
            correlation_id=correlation_id
        )
