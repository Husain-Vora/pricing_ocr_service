"""
S3Service: validate and retrieve a private object by object key; expose
bytes/temp-path plus safe metadata.
"""
import mimetypes
import os
import tempfile
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable, Optional

from botocore.client import BaseClient
from botocore.exceptions import ClientError

from app.core.errors import (
    AppError,
    NotImplementedYetError,
    ObjectTooLargeError,
    S3ObjectNotFoundError,
    UnsupportedFileTypeError,
    ValidationAppError,
)
from app.core.logging import get_logger

logger = get_logger(__name__)

# Codes S3/boto3 use to signal "does not exist" — varies by call and by
# whether the bucket has ListBucket permission for 404 vs 403 disambiguation.
_NOT_FOUND_CODES = {"404", "NoSuchKey", "NotFound"}


@dataclass
class S3ObjectMetadata:
    object_key: str
    content_type: str
    content_length: int


@dataclass
class S3ObjectPayload:
    metadata: S3ObjectMetadata
    local_path: str  # caller is responsible for deleting via finally block


class S3Service(ABC):
    @abstractmethod
    def head_object(self, object_key: str) -> S3ObjectMetadata:
        """Validate existence/type/size without downloading the body."""
        raise NotImplementedError

    @abstractmethod
    def get_object(self, object_key: str) -> S3ObjectPayload:
        """Download to secure temp storage. Caller must delete when done."""
        raise NotImplementedError


class UnimplementedS3Service(S3Service):
    """Stub used until Phase 1 is built and approved."""

    def head_object(self, object_key: str) -> S3ObjectMetadata:
        raise NotImplementedYetError(phase_hint="Phase 1 - S3 retrieval")

    def get_object(self, object_key: str) -> S3ObjectPayload:
        raise NotImplementedYetError(phase_hint="Phase 1 - S3 retrieval")


class BotoS3Service(S3Service):
    """
    Real implementation (Phase 1). Bucket, prefix, size cap and allowed
    content types all come from server-side Settings — never from the
    caller. Credentials are resolved by boto3's default chain (env vars /
    IAM role); no secret keys are handled in this class.
    """

    def __init__(
        self,
        s3_client: BaseClient,
        bucket: str,
        allowed_prefix: str,
        max_object_mb: int,
        allowed_content_types: Iterable[str],
    ) -> None:
        self._client = s3_client
        self._bucket = bucket
        self._allowed_prefix = allowed_prefix
        self._max_bytes = max_object_mb * 1024 * 1024
        self._allowed_content_types = set(allowed_content_types)

    def _validate_key(self, object_key: str) -> str:
        if not object_key or not object_key.strip():
            raise ValidationAppError("object_key must not be empty.")
        key = object_key.strip()
        if key.startswith("/") or ".." in key:
            raise ValidationAppError("object_key is not a valid path.")
        if self._allowed_prefix and not key.startswith(self._allowed_prefix):
            raise ValidationAppError(
                f"object_key must start with the approved prefix '{self._allowed_prefix}'."
            )
        return key

    def _translate_client_error(self, exc: ClientError) -> AppError:
        code = exc.response.get("Error", {}).get("Code", "")
        if code in _NOT_FOUND_CODES:
            return S3ObjectNotFoundError()
        logger.warning("S3 ClientError: code=%s", code)
        return AppError(
            code="S3_ERROR",
            message="The receipt object could not be accessed.",
            status_code=502,
        )

    def head_object(self, object_key: str) -> S3ObjectMetadata:
        key = self._validate_key(object_key)
        try:
            response = self._client.head_object(Bucket=self._bucket, Key=key)
        except ClientError as exc:
            raise self._translate_client_error(exc) from exc

        content_type = response.get("ContentType", "")
        content_length = int(response.get("ContentLength", 0))

        if content_type not in self._allowed_content_types:
            raise UnsupportedFileTypeError(
                f"Content type '{content_type}' is not supported."
            )
        if content_length <= 0:
            raise ValidationAppError("Object is empty.")
        if content_length > self._max_bytes:
            raise ObjectTooLargeError()

        return S3ObjectMetadata(
            object_key=key, content_type=content_type, content_length=content_length
        )

    def get_object(self, object_key: str) -> S3ObjectPayload:
        # Re-validate immediately before download: existence/type/size can
        # change between an earlier head_object call and this one.
        metadata = self.head_object(object_key)

        suffix = mimetypes.guess_extension(metadata.content_type) or ""
        fd, tmp_path = tempfile.mkstemp(prefix="s3obj_", suffix=suffix)
        os.close(fd)
        try:
            self._client.download_file(self._bucket, metadata.object_key, tmp_path)
        except ClientError as exc:
            self._cleanup(tmp_path)
            raise self._translate_client_error(exc) from exc
        except Exception:
            self._cleanup(tmp_path)
            raise

        return S3ObjectPayload(metadata=metadata, local_path=tmp_path)

    @staticmethod
    def _cleanup(path: Optional[str]) -> None:
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                logger.warning("Failed to remove temp file: %s", path)
