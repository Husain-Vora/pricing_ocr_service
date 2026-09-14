from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.pricing import AnomalyLevel


class ReceiptAnalyzeRequest(BaseModel):
    object_key: str = Field(min_length=1, max_length=1024)


class ReceiptAnalysisItem(BaseModel):
    item_name: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    expected_price: Optional[float] = None
    anomaly_score: Optional[float] = Field(default=None, ge=0, le=100)
    anomaly_level: Optional[AnomalyLevel] = None
    extraction_confidence: Optional[float] = Field(default=None, ge=0, le=1)


class ReceiptAnalyzeResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    object_key: str
    model_version: str
    items: List[ReceiptAnalysisItem] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
