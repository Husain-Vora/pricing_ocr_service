from fastapi import APIRouter, Depends

from app.api.dependencies import get_pricing_service
from app.core.security import verify_api_key
from app.schemas.pricing import PricingScoreRequest, PricingScoreResponse
from app.services.pricing_service import PricingService

router = APIRouter(prefix="/api/v1/pricing", tags=["pricing"])


@router.post(
    "/score",
    response_model=PricingScoreResponse,
    dependencies=[Depends(verify_api_key)],
)
def score_price(
    payload: PricingScoreRequest,
    pricing_service: PricingService = Depends(get_pricing_service),
) -> PricingScoreResponse:
    return pricing_service.score(
        name=payload.name, category=payload.category, price=payload.price
    )
