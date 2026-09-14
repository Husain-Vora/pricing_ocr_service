import os

from fastapi import APIRouter, Depends

from app.api.dependencies import get_nlp_service, get_ocr_service, get_s3_service
from app.core.security import verify_api_key
from app.schemas.ocr import OCRExtractRequest, OCRExtractResponse
from app.services.nlp_service import NLPService
from app.services.ocr_service import OCRService
from app.services.s3_service import S3Service

router = APIRouter(prefix="/api/v1/ocr", tags=["ocr"])


@router.post(
    "/extract",
    response_model=OCRExtractResponse,
    dependencies=[Depends(verify_api_key)],
)
def extract_ocr(
    payload: OCRExtractRequest,
    s3_service: S3Service = Depends(get_s3_service),
    ocr_service: OCRService = Depends(get_ocr_service),
    nlp_service: NLPService = Depends(get_nlp_service),
) -> OCRExtractResponse:
    # S3 fetch, OCR and NLP each stay independent, unit-testable modules;
    # this route only sequences the calls and shapes the response.
    s3_service.head_object(payload.object_key)
    payload_bytes = s3_service.get_object(payload.object_key)
    local_path = payload_bytes.local_path
    try:
        ocr_result = ocr_service.extract_text(
            local_path=local_path, content_type=payload_bytes.metadata.content_type
        )
        full_text = "\n".join(page.text for page in ocr_result.pages)
        items = nlp_service.parse_line_items(full_text)
        avg_confidence = (
            sum(p.confidence for p in ocr_result.pages) / len(ocr_result.pages)
            if ocr_result.pages
            else None
        )
        return OCRExtractResponse(
            object_key=payload.object_key,
            document_type=ocr_result.document_type,
            page_count=ocr_result.page_count,
            ocr_confidence=avg_confidence,
            items=items,
            warnings=ocr_result.warnings,
        )
    finally:
        if local_path and os.path.exists(local_path):
            os.remove(local_path)
