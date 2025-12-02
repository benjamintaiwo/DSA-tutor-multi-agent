# AI DS & Algorithm Tutor - Setup Instructions

## Quick Start

### 1. Set up your Google API Key

You need a Gemini API key. Get it from: https://aistudio.google.com/apikey

Then set it as an environment variable:

```bash
export GOOGLE_API_KEY="your-api-key-here"
```

### 2. Create and activate virtual environment

```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the tutor

```bash
python main.py
```

## Environment Variables

```bash
# Required
export GOOGLE_API_KEY="your-gemini-api-key"

# Optional
export GOOGLE_CLOUD_PROJECT="your-project-id"  # For Vertex AI features
export GOOGLE_CLOUD_LOCATION="us-central1"
export USE_PERSISTENT_MEMORY="false"  # Set to "true" for production
export LEETCODE_MCP_SERVER_URL=""  # Optional MCP server
```

## Troubleshooting

**Error: "No module named 'google.adk'"**
- Make sure virtual environment is activated: `source venv/bin/activate`
- Reinstall: `pip install -r requirements.txt`

**Error: "Either app or both app_name and agent must be provided"**
- Make sure you're using the latest version of the code
- Check that `tutor/agent.py` has the Runner initialized correctly

**Error: No API key found**
- Set `GOOGLE_API_KEY` environment variable
- Or use Google Cloud credentials: `gcloud auth application-default login`
