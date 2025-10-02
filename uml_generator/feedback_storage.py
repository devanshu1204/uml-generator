import redis
import json
import uuid
import os
from datetime import datetime
from typing import List, Dict, Any

class FeedbackStorage:
    """Simple Redis-based feedback storage"""
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=int(os.getenv("REDIS_FEEDBACK_DB", 1)),
            decode_responses=True
        )
    
    def store_feedback(self, feedback_data: Dict[str, Any]) -> str:
        """Store feedback with auto-generated ID"""
        feedback_id = str(uuid.uuid4())
        feedback_data["feedback_id"] = feedback_id
        feedback_data["stored_at"] = datetime.now().isoformat()
        
        # Store in Redis
        key = f"feedback:{feedback_id}"
        self.redis_client.set(key, json.dumps(feedback_data))
        
        # Add to index for easy retrieval
        self.redis_client.lpush("feedback:all", feedback_id)
        
        return feedback_id
    
    def get_all_feedback(self) -> List[Dict[str, Any]]:
        """Get all feedback entries"""
        feedback_ids = self.redis_client.lrange("feedback:all", 0, -1)
        results = []
        
        for fid in feedback_ids:
            data = self.redis_client.get(f"feedback:{fid}")
            if data:
                results.append(json.loads(data))
        
        return results
    
    def export_to_json(self, filepath: str):
        """Export all feedback to JSON file"""
        data = self.get_all_feedback()
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        return len(data)

