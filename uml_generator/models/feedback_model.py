from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class FeedbackRequest(BaseModel):
    """Simple feedback request"""
    session_id: str
    diagram_index: int = Field(..., description="Index of diagram in response (0-based)")
    feedback: str = Field(..., description="thumbs_up or thumbs_down")
    comments: Optional[str] = None

