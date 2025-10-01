from typing import List, Dict, Any
from datetime import datetime
from uml_generator.models.request_model import DiagramRequest
from uml_generator.models.response_model import DiagramResponse
import redis
import json
import os

class SessionMemory:
    """Redis-based session memory with TTL"""
    def __init__(self, session_id: str, ttl: int = 3600):
        """
        Initialize Redis session memory
        
        Args:
            session_id: Unique session identifier
            ttl: Time-to-live in seconds (default: 3600 = 1 hour)
        """
        self.session_id = session_id
        self.ttl = ttl
        self.redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=int(os.getenv("REDIS_DB", 0)),
            decode_responses=True
        )
        self.key = f"session:{session_id}"
    
    def add_request(self, request: DiagramRequest):
        """Add a user request to history"""
        history = self.get_history()
        history.append({
            "type": "request",
            "timestamp": datetime.now().isoformat(),
            "prompt": request.prompt,
            "diagram_types": [dt.value for dt in request.diagram_types] if request.diagram_types else None
        })
        self.redis_client.setex(self.key, self.ttl, json.dumps(history))
    
    def add_response(self, response: DiagramResponse):
        """Add a diagram response to history"""
        history = self.get_history()
        history.append({
            "type": "response",
            "timestamp": response.timestamp,
            "diagram_type": response.diagram_type.value,
            "plantuml_code": response.plantuml_code,
            "image_path": response.image_path,
            "token_usage": response.token_usage
        })
        self.redis_client.setex(self.key, self.ttl, json.dumps(history))
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Get full session history"""
        data = self.redis_client.get(self.key)
        return json.loads(data) if data else []
    
    def clear(self):
        """Clear session history"""
        self.redis_client.delete(self.key)