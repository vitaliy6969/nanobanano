"""Request schemas for API endpoints"""

from typing import Optional

from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    """Request schema for image generation"""

    description: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        description="User's description of the desired image (any language)"
    )
    width: int = Field(
        default=1024,
        ge=256,
        le=2048,
        description="Image width in pixels"
    )
    height: int = Field(
        default=1024,
        ge=256,
        le=2048,
        description="Image height in pixels"
    )
    style: Optional[str] = Field(
        default=None,
        description="Optional style preset for image generation"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "description": "Котик, що грає на піаніно в стилі Ван Гога",
                "width": 1024,
                "height": 1024,
                "style": "artistic"
            }
        }


class EditRequest(BaseModel):
    """Request schema for image editing"""

    image_url: Optional[str] = Field(
        default=None,
        description="URL of the image to edit"
    )
    image_base64: Optional[str] = Field(
        default=None,
        description="Base64-encoded image data"
    )
    edit_description: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        description="Description of the changes to make (any language)"
    )
    width: int = Field(
        default=1024,
        ge=256,
        le=4096,
        description="Result image width in pixels"
    )
    height: int = Field(
        default=1024,
        ge=256,
        le=4096,
        description="Result image height in pixels"
    )
    original_prompt: Optional[str] = Field(
        default=None,
        description="Original prompt used to create the image (for context)"
    )
    strength: float = Field(
        default=0.8,
        ge=0.1,
        le=1.0,
        description="How much to modify the image (0.1-1.0)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "image_url": "https://example.com/image.jpg",
                "edit_description": "Змінити фон на зоряне небо",
                "strength": 0.7
            }
        }
