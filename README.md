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
---

## 📖 Overview

This UML Diagram Generator leverages AI to transform natural language descriptions into professional UML diagrams. It uses:

- **Together AI** (Kimi-K2-Instruct model) for intelligent diagram generation
- **PlantUML** for rendering high-quality diagram images
- **Redis** for session-based conversation memory
- **FastAPI** for a RESTful API interface

### Key Features

✅ **14 UML Diagram Types** - Supports all standard UML diagrams  
✅ **Natural Language Input** - Describe your system in plain English  
✅ **Session Memory** - Maintains context across multiple requests  
✅ **Iterative Editing** - Refine diagrams with follow-up instructions  
✅ **REST API** - Easy integration with other tools  
✅ **Batch Generation** - Generate multiple diagram types at once  
✅ **Auto-Save Images** - PNG images saved automatically

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

### Python Library Usage

```python
from uml_generator.uml_generator import UMLDiagramGenerator
from uml_generator.models.request_model import DiagramRequest, DiagramType
from dotenv import load_dotenv

load_dotenv()

# Initialize generator
generator = UMLDiagramGenerator()

# Create request
request = DiagramRequest(
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
    ]
)

# Generate diagrams
responses = generator.generate_diagrams(
    request=request,
    session_id="user_123",
    save_images=True
)

# View results
for response in responses:
    print(f"✓ {response.diagram_type.value} diagram generated")
    print(f"  Image: {response.image_path}")
    print(f"  Tokens: {response.token_usage['total_tokens']}")
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

#### 6. Health Check

```bash
GET /health
```

### Example cURL Request

```bash
curl -X POST "http://localhost:8000/generate/user_123" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a class diagram for a library management system",
    "diagram_types": ["class"]
  }'
```

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
│   └── models/               # Data models
│       ├── diagram_type.py   # Diagram type enum
│       ├── request_model.py  # Request models
│       └── response_model.py # Response models
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
