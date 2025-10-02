# UML Diagram Generator 🎨

An intelligent UML diagram generator that converts natural language descriptions into professional UML diagrams using AI. Supports all 14 standard UML diagram types with session-based context management.

---

## 🚀 Quick Setup Guide

Get started in under 5 minutes!

### 1. Clone and Install

```bash
# Create virtual environment (optional but recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Set Up Redis

The system uses Redis for session management. Install and start Redis:

**macOS:**
```bash
brew install redis
brew services start redis
```

**Linux:**
```bash
sudo apt-get install redis-server
sudo systemctl start redis
```

**Windows:**
Download from [Redis Windows Release](https://github.com/microsoftarchive/redis/releases)

### 3. Configure API Key

Create a `.env` file in the project root:

```bash
# .env
TOGETHER_API_KEY=your-together-ai-api-key-here

# Optional Redis configuration (defaults shown)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

Get your Together AI API key from: https://api.together.xyz/

### 4. Start the API Server (Optional)

```bash
python api_server.py
```

**Test the system with these curl commands:**

1. Generate system data model and diagram:
```bash
curl --location 'http://localhost:8000/v2/generate/:session_id' \
--header 'Content-Type: application/json' \
--data '{
    "prompt": "E-commerce system with users, products, cart, checkout",
    "diagram_types": ["sequence"]
}'
```

2. Switch to a different view without any LLM calls using the previously generated system model:
```bash
curl --location 'http://localhost:8000/v2/switch-view/:session_id' \
--header 'Content-Type: application/json' \
--data '{
    "diagram_type": "class"
}'
```

---

## 📖 Overview

This UML Diagram Generator leverages AI to transform natural language descriptions into professional UML diagrams. It uses a **canonical model-based architecture** inspired by Notion's database-view approach:

> **Extract Once, Render Many Views** - One LLM call creates a comprehensive system model, then templates instantly generate any diagram type.

**Technologies:**
- **Together AI** (Kimi-K2-Instruct model) for intelligent model extraction
- **PlantUML** for rendering high-quality diagram images
- **Redis** for persistent model storage
- **Jinja2 Templates** for diagram rendering
- **FastAPI** for a RESTful API interface

### Key Features

✅ **14 UML Diagram Types** - Supports all standard UML diagrams  
✅ **Natural Language Input** - Describe your system in plain English  
✅ **Canonical Model Architecture** - One model, infinite diagram views  
✅ **Instant View Switching** - Change diagram types with ZERO LLM calls  
✅ **Session Memory** - Maintains context across multiple requests  
✅ **Consistent Data** - All diagrams share the same underlying model  
✅ **Cost Efficient** - Lower token usage, faster rendering  
✅ **Template-Based** - Easy to customize and extend  
✅ **Auto-Save Images** - PNG images saved automatically

### Architecture

```
User Prompt → LLM → Canonical System Model → Templates → PlantUML Diagrams
                          ↓
                    Redis Storage
```

For detailed architecture information, see [ARCHITECTURE.md](ARCHITECTURE.md)

---

## 🎯 Supported Diagram Types

### Structure Diagrams
| Type | Use Case |
|------|----------|
| `class` | Classes, attributes, operations, relationships |
| `object` | Runtime object instances and relationships |
| `component` | High-level system components and interfaces |
| `composite_structure` | Internal structure of classes/components |
| `deployment` | Physical deployment architecture (nodes, containers) |
| `package` | Package organization and dependencies |
| `profile` | UML customization with stereotypes |

### Behavior Diagrams
| Type | Use Case |
|------|----------|
| `use_case` | System functionality and actors |
| `activity` | Workflows, algorithms, business processes |
| `state_machine` | Object lifecycles and state transitions |

### Interaction Diagrams
| Type | Use Case |
|------|----------|
| `sequence` | Time-ordered message interactions |
| `communication` | Network-style interaction view |
| `interaction_overview` | High-level interaction storyboards |
| `timing` | State changes over time |

---

## 💻 Usage

### Python Library Usage (Recommended: Model-Based Approach)

```python
from uml_generator.model_based_generator import ModelBasedGenerator
from uml_generator.models.diagram_type import DiagramType
from dotenv import load_dotenv

load_dotenv()

# Initialize generator
generator = ModelBasedGenerator()

# Generate diagrams (ONE LLM call extracts canonical model)
responses, model, tokens = generator.generate_diagrams(
    prompt="""
    Design an e-commerce system with:
    - User authentication and authorization
    - Product catalog with search
    - Shopping cart functionality
    - Payment processing with multiple gateways
    - Order management and tracking
    """,
    diagram_types=[
        DiagramType.CLASS,
        DiagramType.SEQUENCE,
        DiagramType.COMPONENT
    ],
    session_id="user_123"
)

# View results
print(f"✓ Canonical model generated with {len(model.components)} components")
print(f"  Total tokens used: {tokens['total_tokens']}")

for response in responses:
    print(f"\n✓ {response.diagram_type.value} diagram rendered")
    print(f"  Image: {response.image_path}")
    print(f"  Template rendering tokens: {response.token_usage['total_tokens']}")  # Always 0!
```

### Switch Diagram Views (ZERO LLM Calls!)

```python
# Later, switch to a different diagram type - NO LLM call needed!
state_diagram = generator.switch_diagram_view(
    session_id="user_123",
    new_diagram_type=DiagramType.STATE_MACHINE
)

print(f"✓ State diagram rendered instantly")
print(f"  Tokens used: {state_diagram.token_usage['total_tokens']}")  # 0!
```

### Legacy Approach (Still Supported)

<details>
<summary>Click to expand legacy UMLDiagramGenerator usage</summary>

```python
from uml_generator.uml_generator import UMLDiagramGenerator
from uml_generator.models.request_model import DiagramRequest, DiagramType

generator = UMLDiagramGenerator()

request = DiagramRequest(
    prompt="Design an e-commerce system...",
    diagram_types=[DiagramType.CLASS, DiagramType.SEQUENCE]
)

responses = generator.generate_diagrams(request, session_id="user_123")
# Note: This makes ONE LLM call PER diagram type (less efficient)
```

⚠️ **Note:** The legacy generator makes one LLM call per diagram type. For better efficiency and consistency, use `ModelBasedGenerator` instead.
</details>
```

### Iterative Editing

```python
# Initial generation
request = DiagramRequest(
    prompt="Design a payment processing system",
    diagram_types=[DiagramType.SEQUENCE]
)
responses = generator.generate_diagrams(request, session_id="user_123")

# Edit the diagram
edit_request = DiagramRequest(
    prompt="Add error handling for failed transactions"
    # Note: No diagram_types means edit mode
)
updated = generator.generate_diagrams(edit_request, session_id="user_123")
```

### Session Management

```python
# Get session history
history = generator.get_session_history("user_123")
print(f"Session has {len(history)} items")

# Clear session
generator.clear_session("user_123")
```

---

## 🌐 REST API Usage

### Start the Server

```bash
python api_server.py
```

The API will be available at `http://localhost:8000`

### API Endpoints

#### 1. Generate Diagrams

```bash
POST /generate/{session_id}
```

**Request:**
```json
{
  "prompt": "Design a microservices architecture for a food delivery app",
  "diagram_types": ["component", "sequence", "deployment"]
}
```

**Response:**
```json
[
  {
    "diagram_type": "component",
    "plantuml_code": "@startuml\n...\n@enduml",
    "image_path": "output_diagrams/user_1_component_20251001_120000_0.png",
    "timestamp": "2025-10-01T12:00:00",
    "token_usage": {
      "prompt_tokens": 450,
      "completion_tokens": 823,
      "total_tokens": 1273
    }
  }
]
```

#### 2. Get Available Diagram Types

```bash
GET /diagram-types
```

#### 3. Get Session History

```bash
GET /session-history/{session_id}
```

#### 4. Clear Session

```bash
DELETE /session-history/{session_id}
```

#### 5. Retrieve Diagram Image

```bash
GET /diagram/{filename}
```

#### 6. Submit Feedback (for RL Training)

```bash
POST /feedback
```

**Request:**
```json
{
  "session_id": "user_123",
  "diagram_index": 0,
  "feedback": "thumbs_up",
  "comments": "Great diagram!"
}
```

**Response:**
```json
{
  "message": "Feedback stored successfully",
  "feedback_id": "a1b2c3d4-5678-90ef-ghij-klmnopqrstuv"
}
```

#### 7. Export RL Training Data

```bash
GET /feedback/export?output_file=training_data.json
```

**Response:**
```json
{
  "message": "Feedback exported successfully",
  "output_file": "training_data.json",
  "total_entries": 150
}
```

#### 8. Health Check

```bash
GET /health
```

### Example cURL Requests

**Generate Diagram:**
```bash
curl -X POST "http://localhost:8000/generate/user_123" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a class diagram for a library management system",
    "diagram_types": ["class"]
  }'
```

**Submit Feedback:**
```bash
curl -X POST "http://localhost:8000/feedback" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "user_123",
    "diagram_index": 0,
    "feedback": "thumbs_up",
    "comments": "Excellent diagram!"
  }'
```

**Export Training Data:**
```bash
curl "http://localhost:8000/feedback/export?output_file=training_data.json"
```

### RL Training Data Structure

The exported JSON file contains feedback entries with the following structure:

```json
[
  {
    "feedback_id": "uuid",
    "session_id": "user_123",
    "timestamp": "2025-10-01T12:00:00",
    "prompt": "user's original prompt",
    "diagram_type": "sequence",
    "diagram_code": "@startuml\n...\n@enduml",
    "image_path": "output_diagrams/...",
    "feedback": "thumbs_up",
    "reward": 1.0,
    "comments": "optional comments",
    "is_edit": false,
    "stored_at": "2025-10-01T12:05:00"
  }
]
```

**Fields:**
- `feedback_id`: Unique identifier for the feedback entry
- `session_id`: User session identifier
- `timestamp`: When the diagram was generated
- `prompt`: User's input prompt
- `diagram_type`: Type of diagram generated
- `diagram_code`: The PlantUML code generated
- `image_path`: Path to the generated image
- `feedback`: "thumbs_up" or "thumbs_down"
- `reward`: 1.0 for positive, -1.0 for negative
- `comments`: Optional user comments
- `is_edit`: True if this was an edit request
- `stored_at`: When the feedback was stored

---

## 📁 Project Structure

```
task/
├── api_server.py              # FastAPI REST API server
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables (create this)
├── uml_generator/            # Core UML generator package
│   ├── uml_generator.py      # Main generator logic
│   ├── session.py            # Redis session management
│   ├── feedback_storage.py   # RL feedback storage
│   └── models/               # Data models
│       ├── diagram_type.py   # Diagram type enum
│       ├── request_model.py  # Request models
│       ├── response_model.py # Response models
│       └── feedback_model.py # Feedback models
├── nonsense/                 # Documentation & examples
│   ├── example_usage.py      # Usage examples
│   ├── QUICKSTART.md         # Quick start guide
│   └── PROJECT_SUMMARY.md    # Project overview
└── output_diagrams/          # Generated diagram images
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `TOGETHER_API_KEY` | Together AI API key | *Required* |
| `REDIS_HOST` | Redis server host | `localhost` |
| `REDIS_PORT` | Redis server port | `6379` |
| `REDIS_DB` | Redis database number | `0` |

### Generator Options

```python
generator = UMLDiagramGenerator(
    together_api_key="your-key",  # Optional if set in env
    model="moonshotai/Kimi-K2-Instruct-0905"  # AI model to use
)
```

---

## 📊 Example Use Cases

### 1. Compliance Monitoring System

```python
request = DiagramRequest(
    prompt="""
    Compliance monitoring solution that:
    1. Pulls latest regulatory circulars from SEBI
    2. Parses documents into structured clauses
    3. Extracts new compliance requirements
    4. Performs gap analysis with existing setup
    5. Assesses IT and operational impact
    """,
    diagram_types=[DiagramType.SEQUENCE, DiagramType.COMPONENT]
)
```

### 2. Microservices Architecture

```python
request = DiagramRequest(
    prompt="""
    Food delivery platform with:
    - User Service (auth, profiles)
    - Restaurant Service (listings, menus)
    - Order Service (order management)
    - Payment Service (payment processing)
    - Delivery Service (tracking)
    - Notification Service (SMS, email)
    - API Gateway and Service Mesh
    """,
    diagram_types=[DiagramType.COMPONENT, DiagramType.DEPLOYMENT]
)
```

### 3. State Machine Modeling

```python
request = DiagramRequest(
    prompt="""
    Order lifecycle state machine with states:
    Pending → Confirmed → Processing → Shipped → Delivered
    With events: confirm_payment, start_processing, ship_order
    Include cancellation and refund paths
    """,
    diagram_types=[DiagramType.STATE_MACHINE]
)
```

---

## 🐛 Troubleshooting

### Redis Connection Error

**Problem:** `redis.exceptions.ConnectionError`

**Solution:**
```bash
# Check if Redis is running
redis-cli ping  # Should return "PONG"

# Start Redis
brew services start redis  # macOS
sudo systemctl start redis  # Linux
```

### Together AI API Error

**Problem:** `ValueError: Together AI API key must be provided`

**Solution:**
- Verify `.env` file exists with `TOGETHER_API_KEY`
- Check API key is valid at https://api.together.xyz/
- Ensure `.env` file is in the project root

### No Images Generated

**Problem:** PlantUML images not being created

**Solution:**
- Check internet connection (PlantUML uses online server)
- Verify `output_diagrams/` directory exists
- Check PlantUML code for syntax errors in response

### Import Errors

**Problem:** `ModuleNotFoundError`

**Solution:**
```bash
# Reinstall dependencies
pip install -r requirements.txt

# If using virtual environment, activate it first
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
```

---

## 🔐 Security Notes

- Never commit `.env` file to version control
- Keep your Together AI API key secure
- Use environment variables for production deployments
- Configure Redis authentication in production
- Consider rate limiting for the API server

---

## 📚 Additional Resources

- [PlantUML Documentation](https://plantuml.com/)
- [Together AI API Docs](https://docs.together.ai/)
- [UML Specification](https://www.omg.org/spec/UML/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

---

## 🎓 Tips for Best Results

1. **Be Specific**: Include details about entities, relationships, and workflows
2. **Use Examples**: Provide concrete examples of data or scenarios
3. **Iterate**: Start simple, then refine with edit requests
4. **Choose Right Diagrams**: Select diagram types that match your needs
5. **Session Context**: Use consistent session IDs to maintain conversation context

---

## 📝 License

This project is provided as-is for educational and commercial use.

---

## 🤝 Contributing

For bug reports, feature requests, or contributions, please contact the development team.

---

## ✨ Credits

Built with:
- [Together AI](https://www.together.ai/) - AI model inference
- [PlantUML](https://plantuml.com/) - Diagram rendering
- [FastAPI](https://fastapi.tiangolo.com/) - API framework
- [Redis](https://redis.io/) - Session management

---

**Happy Diagramming! 🎨**
