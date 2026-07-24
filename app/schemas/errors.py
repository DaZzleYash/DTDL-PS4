"""Shared error response schemas — owned by Contributor E."""

from datetime import datetime

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standard error body returned by all exception handlers."""

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: int
    error: str
    message: str
    path: str
