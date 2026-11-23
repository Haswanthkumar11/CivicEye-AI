import os
import re
import logging
from typing import Dict, Any, Optional
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


class MediaStorageService:
    """
    Unified Media Storage Service for CivicEye AI.
    Provides persistent cloud storage via Supabase Storage while maintaining
    a high-speed local disk cache for computer vision (YOLO) and audio models.
    """

    def __init__(self):
        self.upload_dir = os.path.abspath(settings.MEDIA_UPLOAD_DIR)
        os.makedirs(self.upload_dir, exist_ok=True)
        self.supabase_url = settings.SUPABASE_URL.rstrip("/") if settings.SUPABASE_URL else ""
        self.supabase_key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_KEY
        self.bucket = settings.SUPABASE_STORAGE_BUCKET or "civiceye-media"

    @property
    def is_cloud_enabled(self) -> bool:
        return bool(self.supabase_url and self.supabase_key and self.bucket)

    def store_file(
        self,
        contents: bytes,
        stored_filename: str,
        mime_type: str,
    ) -> Dict[str, Any]:
        """
        Stores media to local cache and persists to Supabase Storage if configured.
        Returns file_url (public cloud URL or local /uploads/ URL) and canonical local file_path.
        """
        # 1. Always write locally for fast computer vision access
        local_path = os.path.abspath(os.path.join(self.upload_dir, stored_filename))
        if not local_path.startswith(self.upload_dir):
            raise ValueError("Path traversal attempt in stored_filename.")

        with open(local_path, "wb") as f:
            f.write(contents)

        # 2. Upload to Supabase Storage if configured
        if self.is_cloud_enabled:
            remote_path = f"complaints/{stored_filename}"
            upload_endpoint = f"{self.supabase_url}/storage/v1/object/{self.bucket}/{remote_path}"
            headers = {
                "Authorization": f"Bearer {self.supabase_key}",
                "apikey": self.supabase_key,
                "Content-Type": mime_type,
            }

            try:
                with httpx.Client(timeout=15.0) as client:
                    resp = client.post(upload_endpoint, headers=headers, content=contents)
                    if resp.status_code in (200, 201):
                        public_url = (
                            f"{self.supabase_url}/storage/v1/object/public/{self.bucket}/{remote_path}"
                        )
                        logger.info(f"[MediaStorage] Persisted file to Supabase: {public_url}")
                        return {
                            "file_url": public_url,
                            "file_path": local_path,
                            "storage_provider": "supabase",
                            "remote_path": remote_path,
                        }
                    else:
                        logger.warning(
                            f"[MediaStorage] Supabase upload failed with HTTP {resp.status_code}: {resp.text}. "
                            "Using local storage fallback."
                        )
            except Exception as e:
                logger.warning(f"[MediaStorage] Network error uploading to Supabase: {e}. Using local storage fallback.")

        # Local fallback URL
        return {
            "file_url": f"/uploads/{stored_filename}",
            "file_path": local_path,
            "storage_provider": "local",
            "remote_path": None,
        }

    def ensure_local_copy(self, file_url_or_path: str) -> Optional[str]:
        """
        Ensures a file is present on local disk for local computer vision / audio processing.
        If missing from local disk (e.g. after container restart), fetches it from Supabase Storage.
        """
        if not file_url_or_path:
            return None

        # Extract filename
        fname = os.path.basename(file_url_or_path.split("?")[0])
        local_path = os.path.abspath(os.path.join(self.upload_dir, fname))

        # Check if local file already exists
        if os.path.isfile(local_path) and os.path.getsize(local_path) > 0:
            return local_path

        # If not on local disk and Supabase is configured, attempt download
        if self.is_cloud_enabled:
            remote_candidates = [
                f"complaints/{fname}",
                fname,
            ]
            for remote_path in remote_candidates:
                fetch_url = f"{self.supabase_url}/storage/v1/object/public/{self.bucket}/{remote_path}"
                try:
                    with httpx.Client(timeout=15.0) as client:
                        resp = client.get(fetch_url)
                        if resp.status_code == 200 and len(resp.content) > 0:
                            with open(local_path, "wb") as f:
                                f.write(resp.content)
                            logger.info(f"[MediaStorage] Re-hydrated local cache from Supabase: {fname}")
                            return local_path
                except Exception as e:
                    logger.debug(f"[MediaStorage] Failed to download {remote_path} from Supabase: {e}")

        return local_path if os.path.isfile(local_path) else None


media_storage_service = MediaStorageService()
