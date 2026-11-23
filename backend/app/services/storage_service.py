import os
import shutil
from pathlib import Path
from typing import Optional
from app.config import settings
from app.core.logger import logger

class StorageService:
    """
    S3-Compatible (MinIO / AWS S3) & Local Storage Service.
    Stores input assets, intermediate clips, and final deliverables.
    If S3_ENDPOINT_URL is configured, uploads deliverables to the bucket
    and generates public URLs; otherwise defaults to local /storage.
    """

    def __init__(self):
        self.root = settings.storage_dir
        self.jobs_dir = self.root / "jobs"
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
        self._s3_client = None
        self._init_s3()

    def _init_s3(self):
        if settings.s3_endpoint_url and settings.s3_access_key and settings.s3_secret_key:
            try:
                import boto3
                from botocore.client import Config
                self._s3_client = boto3.client(
                    "s3",
                    endpoint_url=settings.s3_endpoint_url,
                    aws_access_key_id=settings.s3_access_key,
                    aws_secret_access_key=settings.s3_secret_key,
                    region_name=settings.s3_region,
                    config=Config(signature_version="s3v4")
                )
                # Ensure bucket exists / endpoint is reachable
                try:
                    self._s3_client.head_bucket(Bucket=settings.s3_bucket_name)
                except Exception:
                    try:
                        self._s3_client.create_bucket(Bucket=settings.s3_bucket_name)
                        logger.info(f"Created S3/MinIO bucket '{settings.s3_bucket_name}'")
                    except Exception as e:
                        logger.warning(f"Could not reach S3/MinIO endpoint ({e}). Disabling S3 upload and using local storage.")
                        self._s3_client = None
                        return
                logger.info(f"Initialized MinIO/S3 client at {settings.s3_endpoint_url} (bucket: {settings.s3_bucket_name})")
            except Exception as err:
                logger.warning(f"Failed to initialize S3 client ({err}). Using local storage.")
                self._s3_client = None

    def get_job_dir(self, job_id: str) -> Path:
        d = self.jobs_dir / job_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    def upload_file(self, local_path: str, object_key: Optional[str] = None) -> str:
        """
        Uploads file to MinIO/S3 if client is initialized, or confirms local path.
        Returns the public accessible URL.
        """
        path = Path(local_path).resolve()
        if not object_key:
            try:
                rel = path.relative_to(self.root.resolve())
                object_key = str(rel).replace("\\", "/")
            except Exception:
                object_key = path.name

        if self._s3_client:
            try:
                content_type = "video/mp4" if path.suffix == ".mp4" else ("application/json" if path.suffix == ".json" else "text/plain")
                self._s3_client.upload_file(
                    str(path),
                    settings.s3_bucket_name,
                    object_key,
                    ExtraArgs={"ContentType": content_type}
                )
                return f"{settings.s3_endpoint_url}/{settings.s3_bucket_name}/{object_key}"
            except Exception as e:
                logger.warning(f"S3 upload error for {object_key}: {e}. Disabling S3 for subsequent files and using local storage.")
                self._s3_client = None

        return self.get_public_url(str(path))

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
