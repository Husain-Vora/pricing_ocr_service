"""
NLPService: normalize OCR text, detect line items, extract fields and
infer/map category. Real implementation lands in Phase 6.
"""
from abc import ABC, abstractmethod
from typing import List

from app.core.errors import NotImplementedYetError
from app.schemas.ocr import OCRItem


class NLPService(ABC):
    @abstractmethod
    def parse_line_items(self, ocr_text: str) -> List[OCRItem]:
        raise NotImplementedError


class UnimplementedNLPService(NLPService):
    def parse_line_items(self, ocr_text: str) -> List[OCRItem]:
        raise NotImplementedYetError(phase_hint="Phase 6 - NLP line-item extraction")
