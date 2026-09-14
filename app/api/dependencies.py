"""
Dependency-injection wiring.

Routes depend on these functions, never on concrete service classes
directly. Swapping an Unimplemented* stub for a real Phase-N
implementation later changes only this file, not any route.
"""
from functools import lru_cache

from app.services.nlp_service import NLPService, UnimplementedNLPService
from app.services.ocr_service import OCRService, UnimplementedOCRService
from app.services.pricing_service import PricingService, UnimplementedPricingService
from app.services.receipt_analysis_service import (
    ReceiptAnalysisService,
    UnimplementedReceiptAnalysisService,
)
from app.services.s3_service import S3Service, UnimplementedS3Service


@lru_cache
def get_s3_service() -> S3Service:
    return UnimplementedS3Service()


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
