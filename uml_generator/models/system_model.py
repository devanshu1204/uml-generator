"""
Canonical System Model - The single source of truth for all UML diagrams.
This is the "database schema" - all diagram types are just different "views" of this model.

Based on the comprehensive canonical schema that groups related elements together.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class Visibility(str, Enum):
    """Visibility modifiers"""
    PUBLIC = "public"
    PRIVATE = "private"
    PROTECTED = "protected"
    PACKAGE = "package"


class EntityType(str, Enum):
    """Types of entities"""
    CLASS = "class"
    INTERFACE = "interface"
    ABSTRACT = "abstract"
    ENUM = "enum"


class RelationType(str, Enum):
    """Types of relationships between entities"""
    ASSOCIATION = "association"
    AGGREGATION = "aggregation"
    COMPOSITION = "composition"
    INHERITANCE = "inheritance"
    REALIZATION = "realization"
    DEPENDENCY = "dependency"


class MessageType(str, Enum):
    """Types of messages in interactions"""
    SYNC = "sync"
    ASYNC = "async"
    RETURN = "return"
    CREATE = "create"
    DESTROY = "destroy"


class ActorType(str, Enum):
    """Types of actors"""
    HUMAN = "human"
    SYSTEM = "system"


class StateType(str, Enum):
    """Types of states"""
    INITIAL = "initial"
    FINAL = "final"
    SIMPLE = "simple"
    COMPOSITE = "composite"


class NodeType(str, Enum):
    """Types of activity nodes"""
    ACTION = "action"
    DECISION = "decision"
    MERGE = "merge"
    FORK = "fork"
    JOIN = "join"
    INITIAL = "initial"
    FINAL = "final"


class ComponentType(str, Enum):
    """Types of components"""
    COMPONENT = "component"
    PACKAGE = "package"
    SUBSYSTEM = "subsystem"


class DeploymentNodeType(str, Enum):
    """Types of deployment nodes"""
    DEVICE = "device"
    EXECUTION_ENVIRONMENT = "executionEnvironment"
    NODE = "node"
    SYSTEM = "system"  # For external systems


# ============================================================================
# CORE DATA STRUCTURES
# ============================================================================

class SystemMetadata(BaseModel):
    """System metadata"""
    name: str
    description: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Attribute(BaseModel):
    """Entity/Class attribute"""
    name: str
    type: str
    visibility: Visibility = Visibility.PRIVATE
    default: Optional[Any] = None
    isStatic: bool = Field(default=False, alias="is_static")
    
    class Config:
        populate_by_name = True


class Parameter(BaseModel):
    """Method parameter"""
    name: str
    type: str


class Method(BaseModel):
    """Entity/Class method"""
    name: str
    returnType: str = Field(alias="return_type")
    parameters: List[Parameter] = Field(default_factory=list)
    visibility: Visibility = Visibility.PUBLIC
    isStatic: bool = Field(default=False, alias="is_static")
    isAbstract: bool = Field(default=False, alias="is_abstract")
    
    class Config:
        populate_by_name = True


class Entity(BaseModel):
    """Entity (class, interface, abstract class, enum)"""
    id: str
    name: str
    type: EntityType
    stereotype: Optional[str] = None
    attributes: List[Attribute] = Field(default_factory=list)
    methods: List[Method] = Field(default_factory=list)
    description: Optional[str] = None


class Relationship(BaseModel):
    """Relationship between entities"""
    id: str
    type: RelationType
    source: str  # entity_id
    target: str  # entity_id
    sourceCardinality: Optional[str] = Field(default=None, alias="source_cardinality")
    targetCardinality: Optional[str] = Field(default=None, alias="target_cardinality")
    label: Optional[str] = None
    
    class Config:
        populate_by_name = True


class Actor(BaseModel):
    """System actor"""
    id: str
    name: str
    type: ActorType
    description: Optional[str] = None


class UseCase(BaseModel):
    """Use case with full details"""
    id: str
    name: str
    actors: List[str] = Field(default_factory=list)  # actor IDs
    description: Optional[str] = None
    preconditions: List[str] = Field(default_factory=list)
    postconditions: List[str] = Field(default_factory=list)
    mainFlow: List[str] = Field(default_factory=list, alias="main_flow")
    alternativeFlows: List[Dict[str, Any]] = Field(default_factory=list, alias="alternative_flows")
    extends: List[str] = Field(default_factory=list)  # use case IDs
    includes: List[str] = Field(default_factory=list)  # use case IDs
    
    class Config:
        populate_by_name = True


class Message(BaseModel):
    """Message in an interaction"""
    from_: str = Field(alias="from")  # entity_id or actor_id
    to: str  # entity_id or actor_id
    message: str
    order: int
    messageType: MessageType = Field(default=MessageType.SYNC, alias="message_type")
    condition: Optional[str] = None
    returnMessage: Optional[str] = Field(default=None, alias="return_message")
    
    class Config:
        populate_by_name = True


class Interaction(BaseModel):
    """Interaction (sequence or communication diagram)"""
    id: str
    type: str = "sequence"  # sequence | communication
    participants: List[str] = Field(default_factory=list)  # entity/actor IDs
    messages: List[Message] = Field(default_factory=list)
    name: Optional[str] = None


class State(BaseModel):
    """State in a state machine"""
    name: str
    type: StateType
    entry: Optional[str] = None
    exit: Optional[str] = None
    doActivity: Optional[str] = Field(default=None, alias="do_activity")
    
    class Config:
        populate_by_name = True


class StateTransition(BaseModel):
    """Transition between states"""
    from_: str = Field(alias="from")  # state name
    to: str  # state name
    trigger: str
    guard: Optional[str] = None
    action: Optional[str] = None
    
    class Config:
        populate_by_name = True


class StateMachine(BaseModel):
    """State machine for an entity"""
    id: str
    entity: str  # entity_id
    states: List[State] = Field(default_factory=list)
    transitions: List[StateTransition] = Field(default_factory=list)
    name: Optional[str] = None


class ActivityNode(BaseModel):
    """Node in an activity diagram"""
    id: str
    type: NodeType
    name: str
    condition: Optional[str] = None
    swimlane: Optional[str] = None


class ActivityFlow(BaseModel):
    """Flow between activity nodes"""
    from_: str = Field(alias="from")  # node_id
    to: str  # node_id
    guard: Optional[str] = None
    label: Optional[str] = None
    
    class Config:
        populate_by_name = True


class Activity(BaseModel):
    """Activity diagram"""
    id: str
    name: str
    nodes: List[ActivityNode] = Field(default_factory=list)
    flows: List[ActivityFlow] = Field(default_factory=list)


class Component(BaseModel):
    """Component (architectural component, package, subsystem)"""
    id: str
    name: str
    type: ComponentType
    providedInterfaces: List[str] = Field(default_factory=list, alias="provided_interfaces")
    requiredInterfaces: List[str] = Field(default_factory=list, alias="required_interfaces")
    contains: List[str] = Field(default_factory=list)  # entity/component IDs
    stereotype: Optional[str] = None
    
    class Config:
        populate_by_name = True


class DeploymentNode(BaseModel):
    """Deployment node (device, execution environment, node)"""
    id: str
    name: str
    type: DeploymentNodeType
    artifacts: List[str] = Field(default_factory=list)
    nestedNodes: List[str] = Field(default_factory=list, alias="nested_nodes")
    stereotype: Optional[str] = None
    
    class Config:
        populate_by_name = True


# ============================================================================
# CANONICAL SYSTEM MODEL
# ============================================================================

class CanonicalSystemModel(BaseModel):
    """
    The canonical system model - single source of truth.
    All UML diagrams are just different "views" of this model.
    
    This follows the proposed comprehensive schema with grouped elements.
    """
    # System metadata
    system: SystemMetadata
    
    # Core entities (classes, interfaces, enums, abstract classes)
    entities: List[Entity] = Field(default_factory=list)
    
    # Relationships between entities
    relationships: List[Relationship] = Field(default_factory=list)
    
    # Use cases
    useCases: List[UseCase] = Field(default_factory=list, alias="use_cases")
    
    # Actors
    actors: List[Actor] = Field(default_factory=list)
    
    # Interactions (sequence/communication diagrams)
    interactions: List[Interaction] = Field(default_factory=list)
    
    # State machines
    stateMachines: List[StateMachine] = Field(default_factory=list, alias="state_machines")
    
    # Components (architectural)
    components: List[Component] = Field(default_factory=list)
    
    # Deployment nodes
    deploymentNodes: List[DeploymentNode] = Field(default_factory=list, alias="deployment_nodes")
    
    # Activities
    activities: List[Activity] = Field(default_factory=list)
    
    class Config:
        populate_by_name = True
    
    # ========================================================================
    # HELPER METHODS FOR TEMPLATE RENDERING
    # ========================================================================
    
    def get_entity_by_id(self, entity_id: str) -> Optional[Entity]:
        """Get entity by ID"""
        return next((e for e in self.entities if e.id == entity_id), None)
    
    def get_actor_by_id(self, actor_id: str) -> Optional[Actor]:
        """Get actor by ID"""
        return next((a for a in self.actors if a.id == actor_id), None)
    
    def get_component_by_id(self, component_id: str) -> Optional[Component]:
        """Get component by ID"""
        return next((c for c in self.components if c.id == component_id), None)
    
    def get_participant_by_id(self, participant_id: str) -> Optional[Any]:
        """Get participant (actor, entity, or component) by ID"""
        result = self.get_actor_by_id(participant_id)
        if result:
            return result
        result = self.get_entity_by_id(participant_id)
        if result:
            return result
        return self.get_component_by_id(participant_id)
    
    def get_relationships_for_entity(self, entity_id: str) -> List[Relationship]:
        """Get all relationships involving an entity"""
        return [r for r in self.relationships if r.source == entity_id or r.target == entity_id]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for template rendering"""
        data = self.model_dump(by_alias=False)
        # Add helper methods as callable functions
        data['get_entity_by_id'] = self.get_entity_by_id
        data['get_actor_by_id'] = self.get_actor_by_id
        data['get_component_by_id'] = self.get_component_by_id
        data['get_participant_by_id'] = self.get_participant_by_id
        data['get_relationships_for_entity'] = self.get_relationships_for_entity
        return data