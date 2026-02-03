"""Transaction model for logging all image generation requests"""

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, Text, Enum
from sqlalchemy.sql import func

from app.core.database import Base


class TransactionStatus(str, enum.Enum):
    """Status of image generation transaction"""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    ERROR = "error"


class Transaction(Base):
    """
    Transaction model for business memory.

    Stores all image generation/edit requests with their results.
    """

    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Request data
    original_request = Column(Text, nullable=False, comment="Original user request in any language")
    generated_prompt = Column(Text, nullable=True, comment="ChatGPT-generated prompt in English")

    # Operation type
    operation_type = Column(
        String(20),
        nullable=False,
        default="generate",
        comment="Type of operation: generate or edit"
    )

    # Source image (for edit operations)
    source_image_url = Column(String(2048), nullable=True, comment="URL of source image for editing")

    # Result
    status = Column(
        Enum(TransactionStatus),
        nullable=False,
        default=TransactionStatus.PENDING,
        comment="Transaction status"
    )
    result_image_url = Column(Text, nullable=True, comment="URL or base64 data of generated/edited image")
    error_message = Column(Text, nullable=True, comment="Error message if failed")

    # Metadata
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Transaction creation timestamp"
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Last update timestamp"
    )

    # Optional task tracking (for async operations)
    task_id = Column(String(255), nullable=True, comment="External task ID from Nanobanano")

    def __repr__(self):
        return f"<Transaction(id={self.id}, status={self.status}, created_at={self.created_at})>"

    def to_dict(self) -> dict:
        """Convert transaction to dictionary"""
        return {
            "id": self.id,
            "original_request": self.original_request,
            "generated_prompt": self.generated_prompt,
            "operation_type": self.operation_type,
            "source_image_url": self.source_image_url,
            "status": self.status.value if self.status else None,
            "result_image_url": self.result_image_url,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "task_id": self.task_id,
        }
