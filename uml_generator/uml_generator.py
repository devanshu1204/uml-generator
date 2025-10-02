"""
⚠️ LEGACY GENERATOR - Consider using ModelBasedGenerator instead!

This module provides the original UMLDiagramGenerator which makes one LLM call
per diagram type. While still supported, the newer ModelBasedGenerator is recommended:

- ModelBasedGenerator: ONE LLM call → Canonical Model → Many diagram views
- UMLDiagramGenerator: ONE LLM call PER diagram type

For new code, use:
    from uml_generator.model_based_generator import ModelBasedGenerator

See ARCHITECTURE.md for detailed comparison.
"""
from uml_generator.models.request_model import DiagramType, DiagramRequest
from uml_generator.models.response_model import DiagramResponse
from uml_generator.session import SessionMemory
from typing import List, Dict, Any, Optional
import plantuml
import os
from datetime import datetime
from together import Together
import re
import json


class UMLDiagramGenerator:
    """Main UML Diagram Generator class"""
    
    DIAGRAM_DESCRIPTIONS = {
        DiagramType.CLASS: "Class diagrams show classes, attributes, operations, associations, inheritance, composition/aggregation, and interfaces. Used for domain/API design and schemas.",
        DiagramType.OBJECT: "Object diagrams show snapshots of instances at runtime. Great for examples, test fixtures, and clarifying multiplicities.",
        DiagramType.COMPONENT: "Component diagrams show high-level building blocks and provided/required interfaces (ports/lollipops). Used for service/module boundaries.",
        DiagramType.COMPOSITE_STRUCTURE: "Composite Structure diagrams show internal wiring of a class/component: parts, ports, connectors. Used when internals matter.",
        DiagramType.DEPLOYMENT: "Deployment diagrams show runtime topology: nodes (devices/VMs/containers), execution environments, artifacts. Used for ops/DevOps views.",
        DiagramType.PACKAGE: "Package diagrams show namespaces and dependencies. Used for layering and modularization.",
        DiagramType.PROFILE: "Profile diagrams are used for customizing UML (stereotypes, tagged values, constraints). Used to encode domain rules.",
        DiagramType.USE_CASE: "Use Case diagrams show actors and goals; system scope. Used for stakeholder alignment and feature slicing.",
        DiagramType.ACTIVITY: "Activity diagrams show workflow/algorithms: actions, decisions, forks/joins, swimlanes, object flows. Used for business processes and pipelines.",
        DiagramType.STATE_MACHINE: "State Machine diagrams show lifecycles: states, events, guards, entry/exit actions. Used for protocols, UI widgets, order/payment states.",
        DiagramType.SEQUENCE: "Sequence diagrams show time-ordered messages, sync/async, alt/loop fragments. Used for API calls and request lifecycles.",
        DiagramType.COMMUNICATION: "Communication diagrams show the same interaction as sequence but emphasize links between participants; compact network view.",
        DiagramType.INTERACTION_OVERVIEW: "Interaction Overview diagrams are 'storyboards' that stitch other interactions with control flow.",
        DiagramType.TIMING: "Timing diagrams show state/value over time along lifelines; used for real-time, hardware, SLA/timeout analysis."
    }
    
    def __init__(self, together_api_key: Optional[str] = None, model: str = "moonshotai/Kimi-K2-Instruct-0905"):
        """
        Initialize the UML Diagram Generator
        
        Args:
            together_api_key: Together AI API key (if None, will use TOGETHER_API_KEY env variable)
            model: Together AI model to use (default: moonshotai/Kimi-K2-Instruct-0905)
        """
        self.api_key = together_api_key or os.getenv("TOGETHER_API_KEY")
        if not self.api_key:
            raise ValueError("Together AI API key must be provided or set in TOGETHER_API_KEY environment variable")
        
        self.model = model
        self.client = Together(api_key=self.api_key)
        self.plantuml_server = plantuml.PlantUML(url='http://www.plantuml.com/plantuml/img/')
    
    def _create_system_prompt(self, diagram_type: DiagramType) -> str:
        """Create system prompt for a specific diagram type"""
        return f"""You are an expert UML diagram designer. Your task is to generate PlantUML code for a {diagram_type.value.replace('_', ' ').title()} diagram.

        {self.DIAGRAM_DESCRIPTIONS[diagram_type]}

        IMPORTANT INSTRUCTIONS:
        1. Return ONLY the PlantUML code, starting with @startuml and ending with @enduml
        2. Make the diagram comprehensive and detailed based on the user's requirements
        3. Use proper PlantUML syntax for {diagram_type.value.replace('_', ' ')} diagrams
        4. Include relevant details, relationships, and annotations
        5. Make the diagram visually clear and well-organized
        6. Do NOT include any explanations or markdown formatting, ONLY the PlantUML code

        For reference, PlantUML {diagram_type.value.replace('_', ' ')} diagram syntax:
        - Start with @startuml and end with @enduml
        - Use appropriate PlantUML keywords for {diagram_type.value.replace('_', ' ')} diagrams
        - Follow PlantUML best practices for clarity and readability"""
    
    def _generate_single_diagram(self, prompt: str, diagram_type: DiagramType, session_history: List[Dict[str, Any]] = None) -> tuple[str, Dict[str, Any]]:
        """
        Generate a single diagram using Together AI
        
        Args:
            prompt: User's description of the system
            diagram_type: Type of diagram to generate
            session_history: Previous conversation history for context
            
        Returns:
            Tuple of (PlantUML code as string, token usage dict)
        """
        system_prompt = self._create_system_prompt(diagram_type)
        
        # Build messages array with history
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add session history for context
        if session_history:
            for item in session_history:
                if item["type"] == "request":
                    history_prompt = item['prompt']
                    messages.append({"role": "user", "content": history_prompt})
                elif item["type"] == "response":
                    messages.append({"role": "assistant", "content": item["plantuml_code"]})
        
        # Add current request
        user_prompt = f"Generate a {diagram_type.value.replace('_', ' ')} diagram for:\n\n{prompt}"
        messages.append({"role": "user", "content": user_prompt})
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=20000,
        )
        
        plantuml_code = response.choices[0].message.content.strip()
        
        # Extract token usage
        token_usage = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens
        }
        
        # Ensure the code starts with @startuml and ends with @enduml
        if not plantuml_code.startswith("@startuml"):
            plantuml_code = "@startuml\n" + plantuml_code
        if not plantuml_code.endswith("@enduml"):
            plantuml_code = plantuml_code + "\n@enduml"
        
        return plantuml_code, token_usage
    
    def _generate_edit_instructions(self, current_code: str, edit_prompt: str, diagram_type: DiagramType, 
                                   session_history: List[Dict[str, Any]] = None) -> tuple[str, Dict[str, Any]]:
        """
        Generate edit instructions as search-replace blocks
        
        Args:
            current_code: Current PlantUML code
            edit_prompt: User's edit instruction
            diagram_type: Type of diagram being edited
            session_history: Previous conversation history for context
            
        Returns:
            Tuple of (JSON string with search-replace blocks, token usage dict)
        """
        system_prompt = f"""You are an expert UML diagram editor. Your task is to provide PRECISE search-replace instructions to modify PlantUML code.

        IMPORTANT RULES:
        1. Return ONLY a JSON array of edit operations
        2. Each edit must have "search" (exact text to find) and "replace" (new text)
        3. The "search" text must match EXACTLY as it appears in the current code
        4. Be precise - include enough context to make the search unique
        5. Do NOT return the full diagram, ONLY the edits

        Format:
        [
        {{"search": "exact text to find", "replace": "new text"}},
        {{"search": "another exact text", "replace": "replacement"}}
        ]

        Current PlantUML code:
        ```
        {current_code}
        ```
        """

        # Build messages array with history for context
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add session history for context (excluding the current diagram being edited)
        if session_history:
            for item in session_history:
                if item["type"] == "request" and item.get("diagram_types"):
                    # Only include generate requests, not edit requests
                    history_prompt = f"Generate diagrams for: {item['prompt']}"
                    messages.append({"role": "user", "content": history_prompt})
                elif item["type"] == "response":
                    messages.append({"role": "assistant", "content": item["plantuml_code"]})
        
        # Add current edit request
        user_prompt = f"Apply this edit: {edit_prompt}\n\nReturn ONLY the JSON array of search-replace operations."
        messages.append({"role": "user", "content": user_prompt})
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.3,  # Lower temperature for more precise edits
            max_tokens=10000
        )
        
        # Extract token usage
        token_usage = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens
        }
        print(f"Edits: {response.choices[0].message.content.strip()}")
        
        return response.choices[0].message.content.strip(), token_usage
    
    def _apply_edits(self, original_code: str, edits_json: str) -> str:
        """
        Apply search-replace edits to PlantUML code
        
        Args:
            original_code: Original PlantUML code
            edits_json: JSON string with search-replace operations
            
        Returns:
            Modified PlantUML code
        """
        try:
            # Extract JSON from potential markdown code blocks
            json_match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', edits_json, re.DOTALL)
            if json_match:
                edits_json = json_match.group(1)
            
            edits = json.loads(edits_json)
            modified_code = original_code
            
            for edit in edits:
                search_text = edit.get("search", "")
                replace_text = edit.get("replace", "")
                
                if search_text in modified_code:
                    # Replace only the first occurrence to maintain precision
                    modified_code = modified_code.replace(search_text, replace_text, 1)
                    print(f"✓ Applied edit: '{search_text[:50]}...' -> '{replace_text[:50]}...'")
                else:
                    print(f"⚠ Warning: Could not find text to replace: '{search_text[:50]}...'")
            
            return modified_code
        except json.JSONDecodeError as e:
            print(f"Error parsing edit instructions: {e}")
            print(f"LLM Response: {edits_json}")
            raise ValueError("Failed to parse edit instructions from LLM")
    
    def _save_diagram_image(self, plantuml_code: str, diagram_type: DiagramType, session_id: str, index: int = 0) -> str:
        """
        Save PlantUML diagram as an image
        
        Args:
            plantuml_code: PlantUML code
            diagram_type: Type of diagram
            session_id: Session identifier for naming
            index: Index for multiple diagrams of same type
            
        Returns:
            Path to saved image file
        """
        # Create output directory if it doesn't exist
        output_dir = "output_diagrams"
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename with session_id and timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{session_id}_{diagram_type.value}_{timestamp}_{index}.png"
        filepath = os.path.join(output_dir, filename)
        
        # Generate and save image
        try:
            # Write PlantUML code to temporary file
            temp_puml = os.path.join(output_dir, f"temp_{timestamp}_{index}.puml")
            with open(temp_puml, 'w') as f:
                f.write(plantuml_code)
            
            # Generate image using PlantUML server
            image_url = self.plantuml_server.get_url(plantuml_code)
            
            # Download and save image
            import httpx
            response = httpx.get(image_url)
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    f.write(response.content)
            
            # Clean up temp file
            if os.path.exists(temp_puml):
                os.remove(temp_puml)
            
            return filepath
        except Exception as e:
            print(f"Warning: Could not generate image: {e}")
            return None
    
    def generate_diagrams(self, request: DiagramRequest, session_id: str, save_images: bool = True) -> List[DiagramResponse]:
        """
        Generate UML diagrams based on request, or edit existing diagrams
        
        Args:
            request: DiagramRequest with prompt and optional diagram types
            session_id: Unique session identifier
            save_images: Whether to save diagram images (default: True)
            
        Returns:
            List of DiagramResponse objects
        """
        # Create session memory for this session
        session_memory = SessionMemory(session_id)
        
        # Get existing session history for context
        session_history = session_memory.get_history()
        
        # Check if this is an edit request (no diagram_types provided)
        if not request.diagram_types:
            return self._handle_edit_request(request, session_id, session_memory, session_history, save_images)
        
        # Add request to session memory
        session_memory.add_request(request)
        
        responses = []
        
        # Generate each diagram type separately (one LLM call per type)
        for idx, diagram_type in enumerate(request.diagram_types):
            print(f"Generating {diagram_type.value.replace('_', ' ').title()} diagram...")
            
            # Call LLM for this specific diagram type with session history
            plantuml_code, token_usage = self._generate_single_diagram(request.prompt, diagram_type, session_history)
            
            # Save image if requested
            image_path = None
            if save_images:
                image_path = self._save_diagram_image(plantuml_code, diagram_type, session_id, idx)
            
            # Create response
            response = DiagramResponse(
                diagram_type=diagram_type,
                plantuml_code=plantuml_code,
                image_path=image_path,
                token_usage=token_usage
            )
            
            # Add to session memory
            session_memory.add_response(response)
            responses.append(response)
            
            print(f"✓ {diagram_type.value.replace('_', ' ').title()} diagram generated")
            print(f"  Tokens used: {token_usage['prompt_tokens']} input + {token_usage['completion_tokens']} output = {token_usage['total_tokens']} total")
        
        return responses
    
    def _handle_edit_request(self, request: DiagramRequest, session_id: str, session_memory: SessionMemory, 
                            session_history: List[Dict[str, Any]], save_images: bool = True) -> List[DiagramResponse]:
        """
        Handle edit request for the most recent diagram
        
        Args:
            request: DiagramRequest with edit instruction
            session_id: Session identifier
            session_memory: SessionMemory instance
            session_history: Current session history
            save_images: Whether to save images
            
        Returns:
            List with single edited DiagramResponse
        """
        # Find the most recent diagram in history
        last_diagram = None
        for item in reversed(session_history):
            if item["type"] == "response":
                last_diagram = item
                break
        
        if not last_diagram:
            raise ValueError("No previous diagram found to edit. Please generate a diagram first.")
        
        print(f"Editing {last_diagram['diagram_type'].replace('_', ' ').title()} diagram...")
        
        # Get current code and diagram type
        current_code = last_diagram["plantuml_code"]
        diagram_type = DiagramType(last_diagram["diagram_type"])
        
        # Generate edit instructions from LLM with session history
        edits_json, token_usage = self._generate_edit_instructions(current_code, request.prompt, diagram_type, session_history)
        
        # Apply edits
        modified_code = self._apply_edits(current_code, edits_json)
        
        # Save image if requested
        image_path = None
        if save_images:
            image_path = self._save_diagram_image(modified_code, diagram_type, session_id, 0)
        
        # Create response
        response = DiagramResponse(
            diagram_type=diagram_type,
            plantuml_code=modified_code,
            image_path=image_path,
            token_usage=token_usage
        )
        
        # Add to session memory
        session_memory.add_request(request)
        session_memory.add_response(response)
        
        print(f"✓ {diagram_type.value.replace('_', ' ').title()} diagram edited successfully")
        print(f"  Tokens used: {token_usage['prompt_tokens']} input + {token_usage['completion_tokens']} output = {token_usage['total_tokens']} total")
        
        return [response]
    
    def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get session history"""
        session_memory = SessionMemory(session_id)
        return session_memory.get_history()
    
    def clear_session(self, session_id: str):
        """Clear session history"""
        session_memory = SessionMemory(session_id)
        session_memory.clear()
