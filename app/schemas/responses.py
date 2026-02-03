"""Response schemas for API endpoints"""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class TransactionResponse(BaseModel):
    """Response schema for a single transaction"""

    id: int
    original_request: str
    generated_prompt: Optional[str] = None
    operation_type: str
    source_image_url: Optional[str] = None
    status: str
    result_image_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    task_id: Optional[str] = None

    class Config:
        from_attributes = True


class GenerateResponse(BaseModel):
    """Response schema for generation/edit request"""

    success: bool
    transaction_id: int
    message: str
    original_request: str
    generated_prompt: str
    image_url: Optional[str] = None
    status: str

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "transaction_id": 1,
                "message": "Image generated successfully",
                "original_request": "Котик на піаніно",
                "generated_prompt": "A fluffy orange cat playing a grand piano...",
                "image_url": "https://api.nanobanano.pro/images/abc123.png",
                "status": "success"
            }
        }


class HistoryResponse(BaseModel):
    """Response schema for transaction history"""

    total: int = Field(description="Total number of transactions")
    page: int = Field(description="Current page number")
    per_page: int = Field(description="Items per page")
    transactions: List[TransactionResponse]


class ErrorResponse(BaseModel):
    """Standard error response"""

    success: bool = False
    error: str
    detail: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": "Generation failed",
                "detail": "Invalid API key"
            }
        }
