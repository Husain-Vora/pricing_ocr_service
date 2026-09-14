"""
PricingService: normalize product input, run expected-price inference and
calculate the anomaly result. Real model-backed implementation lands in
Phase 3 (model) / Phase 4 (endpoint wiring).
"""
from abc import ABC, abstractmethod

from app.core.errors import NotImplementedYetError
from app.schemas.pricing import PricingScoreResponse


class PricingService(ABC):
    @abstractmethod
    def score(self, name: str, category: str, price: float) -> PricingScoreResponse:
        raise NotImplementedError


class UnimplementedPricingService(PricingService):
    def score(self, name: str, category: str, price: float) -> PricingScoreResponse:
        raise NotImplementedYetError(phase_hint="Phase 3/4 - pricing model")
