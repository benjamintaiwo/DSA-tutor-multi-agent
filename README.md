# AI DS and Algorithm Tutor

An intelligent multi-agent system that orchestrates specialized personas;including a Socratic tutor, a mock interviewer, and a student simulator to help users master data structures and algorithms through adaptive guidance and real-time code execution.

## Features
- **Real LeetCode Integration**: Fetches live problems via GraphQL API or MCP server
- **MCP Support**: Can connect to LeetCode MCP server for enhanced reliability
- **Async Tools**: Tool functions use async/await for efficient I/O
- **Input Validation**: Pydantic schemas validate tool inputs
- **Error Handling**: Comprehensive try/catch with graceful fallbacks
- **Skill Modules**: Pattern Recognition, Constraint Analysis, Example Simulation, Coding Guidance, Meta Reasoning
- **Adaptive Feedback**: Tracks student weaknesses and adjusts teaching strategy
- **Persistent Memory**: Uses Vertex AI Memory Bank for production deployments

## Setup

### 1. Create Virtual Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On macOS/Linux
# OR
venv\Scripts\activate  # On Windows
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Google Cloud
```bash
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_CLOUD_LOCATION="us-central1"
export USE_PERSISTENT_MEMORY="true"  # Set to "false" for testing
export LEETCODE_MCP_SERVER_URL="http://localhost:3000"  # Optional: MCP server
```

### 3. Authenticate
```bash
gcloud auth application-default login
```

## Usage

### Run Locally
```bash
python3 main.py
```

### Example Session
```
You: I want to practice arrays
Tutor: [Fetches a problem like "Two Sum"]
Tutor: Can you explain what this problem is asking?
You: Find two numbers that add up to target
Tutor: Great! What's your approach?
```

## Architecture
- `main.py`: CLI entry point
- `tutor/agent.py`: Wraps `LlmAgent` with `VertexAiMemoryBankService`
- `tutor/orchestrator.py`: Teaching logic and student profile
- `tools/leetcode.py`: LeetCode GraphQL integration

## Memory Persistence

### Development (In-Memory)
```bash
export USE_PERSISTENT_MEMORY="false"
python3 main.py
```

### Production (Vertex AI Memory Bank)
```bash
export USE_PERSISTENT_MEMORY="true"
python3 main.py
```

The tutor will automatically fall back to in-memory storage if Vertex AI is not available.

## Google AI Course Capstone Requirements
-  Uses `google.adk` (LlmAgent, Gemini, Sessions, Memory)
-  Integrates external tool (LeetCode API)
-  Implements state management (TeachingOrchestrator)
-  Demonstrates memory persistence (VertexAiMemoryBankService)
-  Shows adaptive behavior (Skill Module selection based on weaknesses)
