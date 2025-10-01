from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from uml_generator.uml_generator import UMLDiagramGenerator
from uml_generator.models.request_model import DiagramRequest
from uml_generator.models.response_model import DiagramResponse
from uml_generator.models.request_model import DiagramType
from typing import List
from dotenv import load_dotenv
import os
import uvicorn

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

# Initialize generator (singleton)
generator = None


def get_generator():
    """Get or create UML generator instance"""
    global generator
    if generator is None:
        generator = UMLDiagramGenerator()
    return generator


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


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "api_key_configured": bool(os.getenv("OPENAI_API_KEY"))
    }


if __name__ == "__main__":
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True)
