from enum import Enum

class DiagramType(str, Enum):
    """Enum for the 14 UML diagram types"""
    # Structure diagrams
    CLASS = "class"
    OBJECT = "object"
    COMPONENT = "component"
    COMPOSITE_STRUCTURE = "composite_structure"
    DEPLOYMENT = "deployment"
    PACKAGE = "package"
    PROFILE = "profile"
    
    # Behavior diagrams
    USE_CASE = "use_case"
    ACTIVITY = "activity"
    STATE_MACHINE = "state_machine"
    
    # Interaction diagrams (subset of behavior)
    SEQUENCE = "sequence"
    COMMUNICATION = "communication"
    INTERACTION_OVERVIEW = "interaction_overview"
    TIMING = "timing"