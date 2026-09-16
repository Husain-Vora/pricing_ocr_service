"""
Dependency-injection wiring.

Routes depend on these functions, never on concrete service classes
directly. Swapping an Unimplemented* stub for a real Phase-N
implementation later changes only this file, not any route.
"""
from functools import lru_cache

import boto3

from app.core.config import get_settings
from app.services.nlp_service import NLPService, UnimplementedNLPService
from app.services.ocr_service import OCRService, UnimplementedOCRService
from app.services.pricing_service import PricingService, UnimplementedPricingService
from app.services.receipt_analysis_service import (
    ReceiptAnalysisService,
    UnimplementedReceiptAnalysisService,
)
from app.services.s3_service import BotoS3Service, S3Service


@lru_cache
def get_s3_service() -> S3Service:
    settings = get_settings()
    # boto3 resolves credentials via its default chain (env vars / shared
    # config / IAM role) — no secret key handled or accepted in this app.
    client = boto3.client("s3", region_name=settings.AWS_REGION)
    return BotoS3Service(
        s3_client=client,
        bucket=settings.S3_BUCKET,
        allowed_prefix=settings.S3_ALLOWED_PREFIX,
        max_object_mb=settings.S3_MAX_OBJECT_MB,
        allowed_content_types=settings.S3_ALLOWED_CONTENT_TYPES,
    )


@lru_cache
def get_pricing_service() -> PricingService:
    return UnimplementedPricingService()


@lru_cache
def get_ocr_service() -> OCRService:
    return UnimplementedOCRService()


@lru_cache
def get_nlp_service() -> NLPService:
    return UnimplementedNLPService()


@lru_cache
def get_receipt_analysis_service() -> ReceiptAnalysisService:
    return UnimplementedReceiptAnalysisService(
        s3_service=get_s3_service(),
        ocr_service=get_ocr_service(),
        nlp_service=get_nlp_service(),
        pricing_service=get_pricing_service(),
    )
