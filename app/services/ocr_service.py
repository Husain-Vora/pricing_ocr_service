"""
OCRService: convert a supported document to page images, preprocess and
run Tesseract; return OCR pages/confidence. Real implementation lands in
Phase 5 (foundation) / Phase 7 (endpoint wiring).
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List

from app.core.errors import NotImplementedYetError


@dataclass
class OCRPageResult:
    page_number: int
    text: str
    confidence: float


@dataclass
class OCRRawResult:
    document_type: str
    page_count: int
    pages: List[OCRPageResult] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class OCRService(ABC):
    @abstractmethod
    def extract_text(self, local_path: str, content_type: str) -> OCRRawResult:
        raise NotImplementedError


class UnimplementedOCRService(OCRService):
    def extract_text(self, local_path: str, content_type: str) -> OCRRawResult:
        raise NotImplementedYetError(phase_hint="Phase 5/7 - OCR foundation")
