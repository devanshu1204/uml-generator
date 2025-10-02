"""
Model Storage - Stores and retrieves canonical system models in Redis
"""
from typing import Optional
from uml_generator.models.system_model import CanonicalSystemModel
import redis
import json
import os


class ModelStorage:
    """Redis-based storage for canonical system models"""
    
    def __init__(self, ttl: int = 7200):  # 2 hours default
        """
        Initialize Redis model storage
        
        Args:
            ttl: Time-to-live in seconds (default: 7200 = 2 hours)
        """
        self.ttl = ttl
        self.redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=int(os.getenv("REDIS_DB", 0)),
            decode_responses=True
        )
    
    def save_model(self, session_id: str, model: CanonicalSystemModel):
        """
        Save a canonical system model for a session
        
        Args:
            session_id: Unique session identifier
            model: CanonicalSystemModel instance
        """
        key = f"model:{session_id}"
        model_json = model.model_dump_json()
        self.redis_client.setex(key, self.ttl, model_json)
        print(f"✓ Saved canonical model for session: {session_id}")
    
    def get_model(self, session_id: str) -> Optional[CanonicalSystemModel]:
        """
        Retrieve a canonical system model for a session
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            CanonicalSystemModel instance or None if not found
        """
        key = f"model:{session_id}"
        model_json = self.redis_client.get(key)
        
        if model_json:
            return CanonicalSystemModel.model_validate_json(model_json)
        return None
    
    def model_exists(self, session_id: str) -> bool:
        """
        Check if a model exists for a session
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            True if model exists, False otherwise
        """
        key = f"model:{session_id}"
        return self.redis_client.exists(key) > 0
    
    def delete_model(self, session_id: str):
        """
        Delete a model for a session
        
        Args:
            session_id: Unique session identifier
        """
        key = f"model:{session_id}"
        self.redis_client.delete(key)
        print(f"✓ Deleted model for session: {session_id}")
    
    def update_model(self, session_id: str, updates: dict):
        """
        Update specific parts of a model (for future use)
        
        Args:
            session_id: Unique session identifier
            updates: Dictionary with fields to update
        """
        model = self.get_model(session_id)
        if model:
            # Update model fields
            for key, value in updates.items():
                if hasattr(model, key):
                    setattr(model, key, value)
            self.save_model(session_id, model)

