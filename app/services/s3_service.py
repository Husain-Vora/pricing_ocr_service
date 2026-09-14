"""
S3Service: validate and retrieve a private object by object key; expose
bytes/temp-path plus safe metadata. Real boto3-backed implementation is
built in Phase 1 — this file only freezes the interface so routes and
other services can depend on it now.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.core.errors import NotImplementedYetError


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
