from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Optional
from uml_generator.models.diagram_type import DiagramType

class DiagramRequest(BaseModel):
    """Request model for UML diagram generation"""
    prompt: str = Field(..., description="User's description of the system/scenario or edit instruction")
    diagram_types: Optional[List[DiagramType]] = Field(None, description="List of diagram types to generate (if None, treats as edit request)")