import shutil
from pathlib import Path
from typing import Optional
from app.config import settings
from app.core.logger import logger

class StorageService:
    """
    S3-Compatible / Local Storage Service.
    Stores input assets, intermediate clips, and final 6 deliverables.
    """

    def __init__(self):
        self.root = settings.storage_dir
        self.jobs_dir = self.root / "jobs"
        self.jobs_dir.mkdir(parents=True, exist_ok=True)

    def get_job_dir(self, job_id: str) -> Path:
        d = self.jobs_dir / job_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    def get_public_url(self, file_path: str) -> str:
        """
        Converts internal file path into accessible HTTP download URL.
        """
        path = Path(file_path).resolve()
        storage_resolved = self.root.resolve()
        try:
            rel = path.relative_to(storage_resolved)
            rel_str = str(rel).replace("\\", "/")
            return f"{settings.base_url}/storage/{rel_str}"
        except Exception:
            return f"{settings.base_url}/storage/{path.name}"

storage_service = StorageService()
