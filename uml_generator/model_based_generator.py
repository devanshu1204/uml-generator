"""
Model-Based UML Generator - Uses canonical system model + Jinja2 templates approach
One model (database), multiple views (diagram types)
"""
from typing import List, Dict, Any, Optional
from together import Together
from uml_generator.models.system_model import CanonicalSystemModel
from uml_generator.models.diagram_type import DiagramType
from uml_generator.models.response_model import DiagramResponse
from uml_generator.model_storage import ModelStorage
from uml_generator.template_renderer import TemplateRenderer
import plantuml
import httpx
import os
import json
import re
from datetime import datetime


class ModelBasedGenerator:
    """
    Generate UML diagrams using the two-phase approach:
    Phase 1: LLM generates canonical system model (ONE call)
    Phase 2: Jinja2 templates transform model into different diagram types (NO LLM calls)
    """
    
    def __init__(self, together_api_key: Optional[str] = None, model: str = "moonshotai/Kimi-K2-Instruct-0905"):
        """
        Initialize the model-based generator
        
        Args:
            together_api_key: Together AI API key
            model: Together AI model to use
        """
        self.api_key = together_api_key or os.getenv("TOGETHER_API_KEY")
        if not self.api_key:
            raise ValueError("Together AI API key must be provided or set in TOGETHER_API_KEY environment variable")
        
        self.model = model
        self.client = Together(api_key=self.api_key)
        self.model_storage = ModelStorage()
        self.template_renderer = TemplateRenderer()
        self.plantuml_server = plantuml.PlantUML(url='http://www.plantuml.com/plantuml/img/')
    
    def _create_model_generation_prompt(self) -> str:
        """Create system prompt for generating canonical model"""
        return """You are an expert system analyst. Your task is to analyze a system description and create a comprehensive canonical system model in JSON format.

This model will be the SINGLE SOURCE OF TRUTH for all UML diagrams. It must be complete enough to generate sequence, class, component, use case, state machine, activity, and deployment diagrams.

IMPORTANT: Return ONLY valid JSON. No markdown, no explanations, ONLY the JSON object.

The JSON should follow this structure:
{
  "system": {
    "name": "System Name",
    "description": "System description",
    "metadata": {}
  },
  
  "entities": [
    {
      "id": "unique_id",
      "name": "Entity Name",
      "type": "class|interface|abstract|enum",
      "stereotype": "optional",
      "attributes": [
        {
          "name": "attributeName",
          "type": "string",
          "visibility": "public|private|protected|package",
          "default": null,
          "isStatic": false
        }
      ],
      "methods": [
        {
          "name": "methodName",
          "returnType": "void",
          "parameters": [{"name": "paramName", "type": "paramType"}],
          "visibility": "public|private|protected|package",
          "isStatic": false,
          "isAbstract": false
        }
      ],
      "description": "optional"
    }
  ],
  
  "relationships": [
    {
      "id": "unique_id",
      "type": "association|aggregation|composition|inheritance|dependency|realization",
      "source": "entity_id",
      "target": "entity_id",
      "sourceCardinality": "1",
      "targetCardinality": "0..*",
      "label": "optional"
    }
  ],
  
  "useCases": [
    {
      "id": "unique_id",
      "name": "Use Case Name",
      "actors": ["actor_id"],
      "description": "description",
      "preconditions": ["precondition 1"],
      "postconditions": ["postcondition 1"],
      "mainFlow": ["step 1", "step 2"],
      "alternativeFlows": [{"name": "Alternative 1", "steps": ["step 1"]}],
      "extends": ["use_case_id"],
      "includes": ["use_case_id"]
    }
  ],
  
  "actors": [
    {
      "id": "unique_id",
      "name": "Actor Name",
      "type": "human|system",
      "description": "optional"
    }
  ],
  
  "interactions": [
    {
      "id": "unique_id",
      "type": "sequence|communication",
      "name": "optional name",
      "participants": ["entity_id", "actor_id"],
      "messages": [
        {
          "from": "entity_id",
          "to": "entity_id",
          "message": "message text",
          "order": 1,
          "messageType": "sync|async|return|create|destroy",
          "condition": "optional",
          "returnMessage": "optional"
        }
      ]
    }
  ],
  
  "stateMachines": [
    {
      "id": "unique_id",
      "entity": "entity_id",
      "name": "optional name",
      "states": [
        {
          "name": "State Name",
          "type": "initial|final|simple|composite",
          "entry": "optional action",
          "exit": "optional action",
          "doActivity": "optional activity"
        }
      ],
      "transitions": [
        {
          "from": "state_name",
          "to": "state_name",
          "trigger": "event",
          "guard": "optional condition",
          "action": "optional action"
        }
      ]
    }
  ],
  
  "components": [
    {
      "id": "unique_id",
      "name": "Component Name",
      "type": "component|package|subsystem",
      "providedInterfaces": ["interface names"],
      "requiredInterfaces": ["interface names"],
      "contains": ["entity_ids"],
      "stereotype": "optional"
    }
  ],
  
  "deploymentNodes": [
    {
      "id": "unique_id",
      "name": "Node Name",
      "type": "device|executionEnvironment|node|system",
      "artifacts": ["artifact names"],
      "nestedNodes": ["node_ids"],
      "stereotype": "optional"
    }
  ],
  
  "activities": [
    {
      "id": "unique_id",
      "name": "Activity Name",
      "nodes": [
        {
          "id": "node_id",
          "type": "action|decision|merge|fork|join|initial|final",
          "name": "node name",
          "condition": "optional",
          "swimlane": "optional"
        }
      ],
      "flows": [
        {
          "from": "node_id",
          "to": "node_id",
          "guard": "optional condition",
          "label": "optional"
        }
      ]
    }
  ]
}

Guidelines:
1. Be comprehensive - include ALL actors, entities, components, relationships, interactions
2. Use consistent IDs (lowercase, underscores, descriptive, e.g., "user", "shopping_cart", "payment_service")
3. CRITICAL: Every ID referenced MUST have a corresponding definition
4. CRITICAL: Use the SAME IDs consistently (if "user" is an actor, use "user" everywhere, not "customer")
5. Infer typical behaviors even if not explicitly stated
6. Entities are classes/interfaces/enums; Components are architectural elements
7. Group related messages into interactions with participants
8. Group related states/transitions into state machines per entity
9. Group related activity nodes/flows into activities
10. For method parameters, use format: [{"name": "paramName", "type": "paramType"}]
11. Return ONLY the JSON, no other text"""
    
    def generate_canonical_model(self, prompt: str) -> tuple[CanonicalSystemModel, Dict[str, Any]]:
        """
        Generate a canonical system model from a user prompt using LLM
        
        Args:
            prompt: User's description of the system
            
        Returns:
            Tuple of (CanonicalSystemModel, token_usage dict)
        """
        system_prompt = self._create_model_generation_prompt()
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Analyze this system and create a comprehensive canonical model:\n\n{prompt}"}
        ]
        
        print("🤖 Generating canonical system model from LLM...")
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=10000,
        )
        
        llm_output = response.choices[0].message.content.strip()
        print(f"LLM Output:\n{llm_output}")
        
        # Extract JSON from potential markdown code blocks
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', llm_output, re.DOTALL)
        if json_match:
            llm_output = json_match.group(1)
        
        # Parse JSON and create model
        try:
            model_data = json.loads(llm_output)
            canonical_model = CanonicalSystemModel(**model_data)
        except json.JSONDecodeError as e:
            print(f"Error parsing LLM output as JSON: {e}")
            print(f"LLM Output:\n{llm_output}")
            raise ValueError("Failed to parse canonical model from LLM output")
        except Exception as e:
            print(f"Error creating CanonicalSystemModel: {e}")
            print(f"Model data: {model_data}")
            raise ValueError(f"Failed to create canonical model: {e}")
        
        # Token usage
        token_usage = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens
        }
        
        print(f"✓ Canonical model generated successfully")
        print(f"  - System: {canonical_model.system.name}")
        print(f"  - Actors: {len(canonical_model.actors)}")
        print(f"  - Entities: {len(canonical_model.entities)}")
        print(f"  - Components: {len(canonical_model.components)}")
        print(f"  - Relationships: {len(canonical_model.relationships)}")
        print(f"  - Use Cases: {len(canonical_model.useCases)}")
        print(f"  - Interactions: {len(canonical_model.interactions)}")
        print(f"  - State Machines: {len(canonical_model.stateMachines)}")
        print(f"  - Activities: {len(canonical_model.activities)}")
        print(f"  Tokens: {token_usage['total_tokens']}")
        
        return canonical_model, token_usage
    
    def _save_diagram_image(self, plantuml_code: str, diagram_type: DiagramType, session_id: str, index: int = 0) -> str:
        """Save PlantUML diagram as an image"""
        output_dir = "output_diagrams"
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{session_id}_{diagram_type.value}_{timestamp}_{index}.png"
        filepath = os.path.join(output_dir, filename)
        
        try:
            image_url = self.plantuml_server.get_url(plantuml_code)
            print(f"Image URL: {image_url}")
            response = httpx.get(image_url)
            print(f"Response image: {response}")
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    f.write(response.content)
            return filepath
        except Exception as e:
            print(f"Warning: Could not generate image: {e}")
            return None
    
    def generate_diagrams(self, prompt: str, diagram_types: List[DiagramType], session_id: str, 
                         save_images: bool = True) -> tuple[List[DiagramResponse], CanonicalSystemModel, Dict[str, Any]]:
        """
        Generate UML diagrams using the two-phase approach
        
        Args:
            prompt: User's description of the system
            diagram_types: List of diagram types to generate
            session_id: Session identifier
            save_images: Whether to save diagram images
            
        Returns:
            Tuple of (List of DiagramResponse, CanonicalSystemModel, token_usage)
        """
        # Phase 1: Generate canonical model (ONE LLM call)
        canonical_model, token_usage = self.generate_canonical_model(prompt)
        
        # Store the model in Redis
        self.model_storage.save_model(session_id, canonical_model)
        
        # Phase 2: Render diagrams using templates (NO LLM calls)
        responses = []
        for idx, diagram_type in enumerate(diagram_types):
            response = self.render_diagram(session_id, diagram_type, save_images, idx)
            if response:
                responses.append(response)
        
        return responses, canonical_model, token_usage
    
    def render_diagram(self, session_id: str, diagram_type: DiagramType, 
                      save_images: bool = True, index: int = 0) -> Optional[DiagramResponse]:
        """
        Render a diagram from stored canonical model (NO LLM call)
        
        Args:
            session_id: Session identifier
            diagram_type: Type of diagram to render
            save_images: Whether to save diagram image
            index: Index for naming
            
        Returns:
            DiagramResponse or None if model not found
        """
        # Get the canonical model from Redis
        canonical_model = self.model_storage.get_model(session_id)
        
        if not canonical_model:
            print(f"⚠ No canonical model found for session: {session_id}")
            return None
        
        # Check if template exists for this diagram type
        if not self.template_renderer.template_exists(diagram_type):
            print(f"⚠ Template not available for diagram type: {diagram_type.value}")
            return None
        
        print(f"📐 Rendering {diagram_type.value} diagram from canonical model...")
        
        # Render PlantUML code using template
        plantuml_code = self.template_renderer.render(canonical_model, diagram_type)
        
        # Save image if requested
        image_path = None
        if save_images:
            image_path = self._save_diagram_image(plantuml_code, diagram_type, session_id, index)
            print(f"Image saved to {image_path}")
        
        # Create response (no token usage for template rendering)
        response = DiagramResponse(
            diagram_type=diagram_type,
            plantuml_code=plantuml_code,
            image_path=image_path,
            token_usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}  # No LLM call!
        )
        
        print(f"✓ {diagram_type.value} diagram rendered (no LLM call)")
        
        return response
    
    def get_supported_diagram_types(self) -> List[DiagramType]:
        """Get list of diagram types supported by templates"""
        return self.template_renderer.get_supported_diagrams()
    
    def switch_diagram_view(self, session_id: str, new_diagram_type: DiagramType, 
                           save_image: bool = True) -> Optional[DiagramResponse]:
        """
        Switch to a different diagram type for the same system (like Notion view switching)
        
        This is the key feature: NO LLM call needed, just apply a different template!
        
        Args:
            session_id: Session identifier
            new_diagram_type: New diagram type to render
            save_image: Whether to save the image
            
        Returns:
            DiagramResponse or None if model not found
        """
        print(f"\n🔄 Switching view to {new_diagram_type.value} diagram (no LLM call)...")
        return self.render_diagram(session_id, new_diagram_type, save_image, 0)

