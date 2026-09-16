import os
from unittest.mock import MagicMock

import boto3
import pytest
from botocore.exceptions import ClientError
from botocore.stub import Stubber

from app.core.errors import (
    ObjectTooLargeError,
    S3ObjectNotFoundError,
    UnsupportedFileTypeError,
    ValidationAppError,
)
from app.services.s3_service import BotoS3Service

BUCKET = "test-bucket"
PREFIX = "org/"
MAX_MB = 1  # 1 MiB cap, easy to exceed in tests
ALLOWED_TYPES = {"application/pdf", "image/png", "image/jpeg"}


@pytest.fixture
def s3_client():
    return boto3.client("s3", region_name="ap-south-1", aws_access_key_id="x", aws_secret_access_key="y")


@pytest.fixture
def service(s3_client):
    return BotoS3Service(
        s3_client=s3_client,
        bucket=BUCKET,
        allowed_prefix=PREFIX,
        max_object_mb=MAX_MB,
        allowed_content_types=ALLOWED_TYPES,
    )


# --- key validation (no AWS call reached) ---


def test_rejects_empty_key(service):
    with pytest.raises(ValidationAppError):
        service.head_object("")


def test_rejects_path_traversal(service):
    with pytest.raises(ValidationAppError):
        service.head_object("org/../../etc/passwd")


def test_rejects_wrong_prefix(service):
    with pytest.raises(ValidationAppError):
        service.head_object("not-approved/receipt.pdf")


# --- head_object against a stubbed S3 client ---


def test_head_object_success(s3_client, service):
    with Stubber(s3_client) as stub:
        stub.add_response(
            "head_object",
            {"ContentType": "application/pdf", "ContentLength": 1024},
            {"Bucket": BUCKET, "Key": "org/1/receipt.pdf"},
        )
        metadata = service.head_object("org/1/receipt.pdf")

    assert metadata.object_key == "org/1/receipt.pdf"
    assert metadata.content_type == "application/pdf"
    assert metadata.content_length == 1024


def test_head_object_not_found_returns_controlled_error(s3_client, service):
    with Stubber(s3_client) as stub:
        stub.add_client_error("head_object", service_error_code="404", http_status_code=404)
        with pytest.raises(S3ObjectNotFoundError):
            service.head_object("org/1/missing.pdf")


def test_head_object_rejects_unsupported_content_type(s3_client, service):
    with Stubber(s3_client) as stub:
        stub.add_response(
            "head_object",
            {"ContentType": "application/zip", "ContentLength": 1024},
            {"Bucket": BUCKET, "Key": "org/1/archive.zip"},
        )
        with pytest.raises(UnsupportedFileTypeError):
            service.head_object("org/1/archive.zip")


def test_head_object_rejects_oversized_object(s3_client, service):
    too_big = (MAX_MB * 1024 * 1024) + 1
    with Stubber(s3_client) as stub:
        stub.add_response(
            "head_object",
            {"ContentType": "application/pdf", "ContentLength": too_big},
            {"Bucket": BUCKET, "Key": "org/1/huge.pdf"},
        )
        with pytest.raises(ObjectTooLargeError):
            service.head_object("org/1/huge.pdf")


# --- get_object: download + temp file lifecycle ---


def test_get_object_success_writes_and_returns_temp_file(s3_client, service):
    written_paths = []

    def fake_download_file(bucket, key, path, *args, **kwargs):
        with open(path, "wb") as f:
            f.write(b"%PDF-1.4 fake content")
        written_paths.append(path)

    service._client.download_file = MagicMock(side_effect=fake_download_file)

    with Stubber(s3_client) as stub:
        stub.add_response(
            "head_object",
            {"ContentType": "application/pdf", "ContentLength": 20},
            {"Bucket": BUCKET, "Key": "org/1/receipt.pdf"},
        )
        payload = service.get_object("org/1/receipt.pdf")

    try:
        assert os.path.exists(payload.local_path)
        assert payload.metadata.content_type == "application/pdf"
    finally:
        os.remove(payload.local_path)


def test_get_object_cleans_temp_file_on_download_failure(s3_client, service):
    def failing_download(bucket, key, path, *args, **kwargs):
        raise ClientError(
            {"Error": {"Code": "404", "Message": "Not Found"}}, "DownloadFile"
        )

    service._client.download_file = MagicMock(side_effect=failing_download)

    with Stubber(s3_client) as stub:
        stub.add_response(
            "head_object",
            {"ContentType": "application/pdf", "ContentLength": 20},
            {"Bucket": BUCKET, "Key": "org/1/receipt.pdf"},
        )
        with pytest.raises(S3ObjectNotFoundError):
            service.get_object("org/1/receipt.pdf")

    # No leaked temp file: nothing left matching our prefix in the temp dir.
    import tempfile

    leaked = [f for f in os.listdir(tempfile.gettempdir()) if f.startswith("s3obj_")]
    assert leaked == []
