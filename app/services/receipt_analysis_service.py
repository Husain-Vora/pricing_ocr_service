"""
ReceiptAnalysisService: orchestrate S3 -> OCR -> NLP -> batch pricing and
aggregate warnings. This calls the other service classes directly in
process; it must never make an HTTP call back into this API's own
/ocr/extract or /pricing/score endpoints. Real implementation lands in
Phase 8.
"""
from abc import ABC, abstractmethod

from app.core.errors import NotImplementedYetError
from app.schemas.receipt import ReceiptAnalyzeResponse
from app.services.nlp_service import NLPService
from app.services.ocr_service import OCRService
from app.services.pricing_service import PricingService
from app.services.s3_service import S3Service


class ReceiptAnalysisService(ABC):
    @abstractmethod
    def analyze(self, object_key: str) -> ReceiptAnalyzeResponse:
        raise NotImplementedError


class UnimplementedReceiptAnalysisService(ReceiptAnalysisService):
    """
    Holds references to the underlying services (constructor DI) so the
    Phase 8 implementation only needs to fill in `analyze`, without
    touching how this service is wired into the API layer.
    """

    def __init__(
        self,
        s3_service: S3Service,
        ocr_service: OCRService,
        nlp_service: NLPService,
        pricing_service: PricingService,
    ) -> None:
        self._s3_service = s3_service
        self._ocr_service = ocr_service
        self._nlp_service = nlp_service
        self._pricing_service = pricing_service

    def analyze(self, object_key: str) -> ReceiptAnalyzeResponse:
        raise NotImplementedYetError(phase_hint="Phase 8 - combined receipt analysis")
