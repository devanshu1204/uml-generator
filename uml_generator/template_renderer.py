"""
Template Renderer - Transforms canonical system models into PlantUML diagrams using Jinja2 templates
"""
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from uml_generator.models.system_model import CanonicalSystemModel
from uml_generator.models.diagram_type import DiagramType
import os


class TemplateRenderer:
    """Renders PlantUML diagrams from canonical models using Jinja2 templates"""
    
    # Map diagram types to template files
    TEMPLATE_MAP = {
        DiagramType.SEQUENCE: "sequence.j2",
        DiagramType.CLASS: "class.j2",
        DiagramType.COMPONENT: "component.j2",
        DiagramType.USE_CASE: "use_case.j2",
        DiagramType.STATE_MACHINE: "state_machine.j2",
        DiagramType.ACTIVITY: "activity.j2",
        DiagramType.DEPLOYMENT: "deployment.j2",
        # Add more as templates are created
    }
    
    def __init__(self, templates_dir: str = None):
        """
        Initialize the template renderer
        
        Args:
            templates_dir: Directory containing Jinja2 templates (default: uml_generator/templates)
        """
        if templates_dir is None:
            # Get the directory of this file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            templates_dir = os.path.join(current_dir, "templates")
        
        self.templates_dir = templates_dir
        self.env = Environment(
            loader=FileSystemLoader(templates_dir),
            trim_blocks=False,
            lstrip_blocks=False
        )
        
        print(f"Template renderer initialized with templates from: {templates_dir}")
    
    def render(self, model: CanonicalSystemModel, diagram_type: DiagramType) -> str:
        """
        Render a PlantUML diagram from a canonical model
        
        Args:
            model: CanonicalSystemModel instance
            diagram_type: Type of diagram to render
            
        Returns:
            PlantUML code as string
            
        Raises:
            TemplateNotFound: If template for diagram type doesn't exist
            ValueError: If diagram type is not supported
        """
        if diagram_type not in self.TEMPLATE_MAP:
            raise ValueError(f"Template not yet implemented for diagram type: {diagram_type.value}")
        
        template_name = self.TEMPLATE_MAP[diagram_type]
        
        try:
            template = self.env.get_template(template_name)
        except TemplateNotFound:
            raise TemplateNotFound(f"Template file not found: {template_name}")
        
        # Render the template with model data
        plantuml_code = template.render(**model.to_dict())
        
        # Clean up extra blank lines
        lines = [line for line in plantuml_code.split('\n')]
        cleaned_lines = []
        prev_blank = False
        
        for line in lines:
            if line.strip() == '':
                if not prev_blank:
                    cleaned_lines.append(line)
                prev_blank = True
            else:
                cleaned_lines.append(line)
                prev_blank = False
        
        return '\n'.join(cleaned_lines)
    
    def get_supported_diagrams(self) -> list[DiagramType]:
        """
        Get list of diagram types that have templates
        
        Returns:
            List of supported DiagramType enums
        """
        return list(self.TEMPLATE_MAP.keys())
    
    def template_exists(self, diagram_type: DiagramType) -> bool:
        """
        Check if a template exists for a diagram type
        
        Args:
            diagram_type: DiagramType to check
            
        Returns:
            True if template exists, False otherwise
        """
        return diagram_type in self.TEMPLATE_MAP

