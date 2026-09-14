from typing import List, Optional

from pydantic import BaseModel, Field


class OCRExtractRequest(BaseModel):
    object_key: str = Field(min_length=1, max_length=1024)


class OCRItem(BaseModel):
    line_no: int
    item_name: Optional[str] = None
    category: Optional[str] = None
    quantity: Optional[float] = None
    price: Optional[float] = None
    extraction_confidence: Optional[float] = Field(default=None, ge=0, le=1)


class OCRExtractResponse(BaseModel):
    object_key: str
    document_type: Optional[str] = None
    page_count: int
    ocr_confidence: Optional[float] = Field(default=None, ge=0, le=1)
    items: List[OCRItem] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
