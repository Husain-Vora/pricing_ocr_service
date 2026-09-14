from fastapi import APIRouter, Depends

from app.api.dependencies import get_receipt_analysis_service
from app.core.security import verify_api_key
from app.schemas.receipt import ReceiptAnalyzeRequest, ReceiptAnalyzeResponse
from app.services.receipt_analysis_service import ReceiptAnalysisService

router = APIRouter(prefix="/api/v1/receipt", tags=["receipt"])


@router.post(
    "/analyze",
    response_model=ReceiptAnalyzeResponse,
    dependencies=[Depends(verify_api_key)],
)
def analyze_receipt(
    payload: ReceiptAnalyzeRequest,
    receipt_analysis_service: ReceiptAnalysisService = Depends(get_receipt_analysis_service),
) -> ReceiptAnalyzeResponse:
    # Orchestration (S3 -> OCR -> NLP -> pricing) lives inside the service,
    # calling the other Python service classes directly — never HTTP back
    # into this API's own /ocr/extract or /pricing/score.
    return receipt_analysis_service.analyze(payload.object_key)
