from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from uml_generator.uml_generator import UMLDiagramGenerator
from uml_generator.model_based_generator import ModelBasedGenerator
from uml_generator.models.request_model import DiagramRequest
from uml_generator.models.response_model import DiagramResponse
from uml_generator.models.request_model import DiagramType
from uml_generator.models.feedback_model import FeedbackRequest
from uml_generator.feedback_storage import FeedbackStorage
from uml_generator.session import SessionMemory
from typing import List, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os
import uvicorn
from datetime import datetime

# Load environment variables
load_dotenv()

app = FastAPI(
    title="UML Diagram Generator API",
    description="Generate UML diagrams from natural language descriptions",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize generator and feedback storage (singletons)
generator = None
model_based_generator = None
feedback_storage = None


def get_generator():
    """Get or create UML generator instance (legacy approach)"""
    global generator
    if generator is None:
        generator = UMLDiagramGenerator()
    return generator


def get_model_based_generator():
    """Get or create Model-Based UML generator instance (new approach)"""
    global model_based_generator
    if model_based_generator is None:
        model_based_generator = ModelBasedGenerator()
    return model_based_generator


def get_feedback_storage():
    """Get or create feedback storage instance"""
    global feedback_storage
    if feedback_storage is None:
        feedback_storage = FeedbackStorage()
    return feedback_storage


# Request/Response models for new endpoints
class ModelBasedRequest(BaseModel):
    """Request for model-based diagram generation"""
    prompt: str = Field(..., description="User's description of the system")
    diagram_types: List[DiagramType] = Field(..., description="Initial diagram types to generate")


class SwitchViewRequest(BaseModel):
    """Request to switch diagram view"""
    diagram_type: DiagramType = Field(..., description="New diagram type to render")


@app.get("/")
async def root():
    """API health check"""
    return {
        "message": "UML Diagram Generator API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/diagram-types")
async def get_diagram_types():
    """Get all supported diagram types"""
    return {
        "diagram_types": [dt.value for dt in DiagramType],
        "total": len(DiagramType),
        "categories": {
            "structure": ["class", "object", "component", "composite_structure", "deployment", "package", "profile"],
            "behavior": ["use_case", "activity", "state_machine"],
            "interaction": ["sequence", "communication", "interaction_overview", "timing"]
        }
    }


@app.post("/generate/{session_id}", response_model=List[DiagramResponse])
async def generate_diagrams(session_id: str, request: DiagramRequest):
    """
    Generate UML diagrams from a prompt
    
    Path parameter:
    - session_id: Unique session identifier
    
    Request body:
    {
        "prompt": "Your system description",
        "diagram_types": ["sequence", "class", ...]
    }
    """
    try:
        gen = get_generator()
        responses = gen.generate_diagrams(request, session_id=session_id, save_images=True)
        return responses
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/session-history/{session_id}")
async def get_session_history(session_id: str):
    """Get session history for a specific session"""
    try:
        gen = get_generator()
        history = gen.get_session_history(session_id)
        return {"session_id": session_id, "history": history, "total_items": len(history)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/session-history/{session_id}")
async def clear_session_history(session_id: str):
    """Clear session history for a specific session"""
    try:
        gen = get_generator()
        gen.clear_session(session_id)
        return {"message": f"Session history cleared successfully for session: {session_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/diagram/{filename}")
async def get_diagram_image(filename: str):
    """Retrieve a generated diagram image"""
    file_path = os.path.join("output_diagrams", filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Diagram image not found")
    
    return FileResponse(file_path, media_type="image/png")


@app.post("/feedback")
async def submit_feedback(feedback: FeedbackRequest):
    """
    Submit user feedback for RL training
    
    Request body:
    {
        "session_id": "user_session_id",
        "diagram_index": 0,
        "feedback": "thumbs_up" or "thumbs_down",
        "comments": "optional comments"
    }
    """
    try:
        # Get session history
        session_memory = SessionMemory(feedback.session_id)
        history = session_memory.get_history()
        
        # Find the diagram
        responses = [item for item in history if item["type"] == "response"]
        requests = [item for item in history if item["type"] == "request"]
        
        if feedback.diagram_index >= len(responses):
            raise HTTPException(status_code=404, detail="Diagram not found")
        
        diagram = responses[feedback.diagram_index]
        request = requests[min(feedback.diagram_index, len(requests) - 1)]
        
        # Create feedback entry
        feedback_data = {
            "session_id": feedback.session_id,
            "timestamp": datetime.now().isoformat(),
            "prompt": request["prompt"],
            "diagram_type": diagram["diagram_type"],
            "diagram_code": diagram["plantuml_code"],
            "image_path": diagram.get("image_path"),
            "feedback": feedback.feedback,
            "reward": 1.0 if feedback.feedback == "thumbs_up" else -1.0,
            "comments": feedback.comments,
            "is_edit": request.get("diagram_types") is None,
            # Add conversation history
            "conversation_history": history[:feedback.diagram_index*2],  # Include previous request-response pairs
            "previous_diagram_code": responses[feedback.diagram_index - 1]["plantuml_code"] if feedback.diagram_index > 0 and feedback_data.get("is_edit") else None
        }
        
        # Store feedback
        storage = get_feedback_storage()
        feedback_id = storage.store_feedback(feedback_data)
        
        return {
            "message": "Feedback stored successfully",
            "feedback_id": feedback_id
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/feedback/export")
async def export_feedback(output_file: str = "rl_training_data.json"):
    """Export all feedback data for RL training"""
    try:
        storage = get_feedback_storage()
        count = storage.export_to_json(output_file)
        
        return {
            "message": "Feedback exported successfully",
            "output_file": output_file,
            "total_entries": count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "api_key_configured": bool(os.getenv("TOGETHER_API_KEY"))
    }


# ============================================================================
# NEW MODEL-BASED ENDPOINTS Version 2 using a json model structure and jinja2 templates
# ============================================================================

@app.post("/v2/generate/{session_id}", response_model=List[DiagramResponse])
async def generate_diagrams_v2(session_id: str, request: ModelBasedRequest):
    """
    Generate UML diagrams using the new model-based approach (v2).

    - Phase 1: ONE LLM call to create canonical system model
    - Phase 2: Jinja2 templates render different diagram views
    
    Path parameter:
    - session_id: Unique session identifier
    
    Request body:
    {
        "prompt": "Your system description",
        "diagram_types": ["sequence", "class", "component", ...]
    }
    
    After this call, you can switch diagram views instantly using /v2/switch-view/{session_id}
    """
    try:
        gen = get_model_based_generator()
        responses, canonical_model, token_usage = gen.generate_diagrams(
            prompt=request.prompt,
            diagram_types=request.diagram_types,
            session_id=session_id,
            save_images=True
        )
        
        print(f"\n✓ Generated {len(responses)} diagram(s) from canonical model")
        print(f"  Total tokens used: {token_usage['total_tokens']} (only for model generation)")
        
        return responses
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v2/switch-view/{session_id}", response_model=DiagramResponse)
async def switch_diagram_view(session_id: str, request: SwitchViewRequest):
    """
    Switch to a different diagram type for the same system - NO LLM CALL NEEDED!
    
    This is like switching from "Table View" to "Kanban View" in Notion.
    The underlying data (canonical model) stays the same, only the view changes.
    
    Path parameter:
    - session_id: Session ID that already has a canonical model
    
    Request body:
    {
        "diagram_type": "component"
    }
    
    This endpoint:
    - Does NOT call the LLM (instant response!)
    - Uses the stored canonical model
    - Applies a different Jinja2 template
    - Ensures consistency (same actors, components, etc.)
    """
    try:
        gen = get_model_based_generator()
        response = gen.switch_diagram_view(
            session_id=session_id,
            new_diagram_type=request.diagram_type,
            save_image=True
        )
        
        if not response:
            raise HTTPException(
                status_code=404,
                detail=f"No canonical model found for session: {session_id}. Please call /v2/generate first."
            )
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v2/available-views/{session_id}")
async def get_available_views(session_id: str):
    """
    Get list of available diagram views for a session
    
    Returns all diagram types that have Jinja2 templates available.
    """
    try:
        gen = get_model_based_generator()
        
        # Check if model exists for this session
        if not gen.model_storage.model_exists(session_id):
            raise HTTPException(
                status_code=404,
                detail=f"No canonical model found for session: {session_id}. Please call /v2/generate first."
            )
        
        supported_types = gen.get_supported_diagram_types()
        
        return {
            "session_id": session_id,
            "available_views": [dt.value for dt in supported_types],
            "total": len(supported_types),
            "note": "You can switch between these views instantly without LLM calls"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v2/canonical-model/{session_id}")
async def get_canonical_model(session_id: str):
    """
    Get the canonical system model for a session (for debugging/inspection)
    """
    try:
        gen = get_model_based_generator()
        model = gen.model_storage.get_model(session_id)
        
        if not model:
            raise HTTPException(
                status_code=404,
                detail=f"No canonical model found for session: {session_id}"
            )
        
        return {
            "session_id": session_id,
            "model": model.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True)
