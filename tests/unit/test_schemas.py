import pytest
from pydantic import ValidationError

from app.schemas.pricing import PricingScoreRequest


def test_pricing_request_rejects_non_positive_price():
    with pytest.raises(ValidationError):
        PricingScoreRequest(name="Mouse", category="Accessories", price=0)


def test_pricing_request_rejects_empty_name():
    with pytest.raises(ValidationError):
        PricingScoreRequest(name="", category="Accessories", price=10)


def test_pricing_request_accepts_valid_payload():
    req = PricingScoreRequest(name="Mouse", category="Accessories", price=1299.0)
    assert req.price == 1299.0
