from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from uml_generator.models.diagram_type import DiagramType


class DiagramResponse(BaseModel):
    """Response model for generated diagram"""
    diagram_type: DiagramType
    plantuml_code: str
    image_path: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    token_usage: Optional[Dict[str, Any]] = Field(None, description="Token usage statistics")