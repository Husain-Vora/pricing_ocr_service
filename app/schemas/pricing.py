from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class AnomalyLevel(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class AnomalyDirection(str, Enum):
    ABOVE = "AboveExpected"
    BELOW = "BelowExpected"
    NEAR = "NearExpected"


class PricingScoreRequest(BaseModel):
    name: str = Field(min_length=1, max_length=300)
    category: str = Field(min_length=1, max_length=150)
    price: float = Field(gt=0, description="Observed price. Must be positive and finite.")


class PricingScoreResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    name: str
    category: str
    observed_price: float
    expected_price: float
    deviation_percent: float
    anomaly_score: float = Field(ge=0, le=100)
    anomaly_level: AnomalyLevel
    direction: AnomalyDirection
    model_version: str
    confidence: Optional[float] = Field(default=None, ge=0, le=1)
