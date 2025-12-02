import os
import json
from enum import Enum
from typing import Optional, Dict, Any
from google.adk.models.google_llm import Gemini
from google.genai import types

class AgentMode(str, Enum):
    TUTOR = "TUTOR"
    INTERVIEWER = "INTERVIEWER"
    STUDENT = "STUDENT"

ROUTER_PROMPT = """You are the Orchestrator for an AI Coding Tutor.
Your job is to route the user's request to the correct specialized agent.

Available Agents:
1. TUTOR: The default mode. Helps students solve problems, gives hints, explains concepts.
2. INTERVIEWER: Conducts a strict technical interview. Use this if the user asks to be interviewed.
3. STUDENT: A simulated beginner student. Use this if the user wants to "teach" or "explain" to the AI.

Output strictly valid JSON:
{
    "target_agent": "TUTOR" | "INTERVIEWER" | "STUDENT",
    "reasoning": "brief explanation"
}

User Input: """

class IntentRouter:
    def __init__(self, project_id: str, location: str):
        # Use a fast, lightweight model for routing
        retry_config = types.HttpRetryOptions(attempts=3, initial_delay=1)
        api_key = os.getenv("GOOGLE_API_KEY")
        
        if api_key:
             self.model = Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config, api_key=api_key)
        else:
             self.model = Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config, project=project_id, location=location, vertexai=True)

    def route(self, user_input: str, current_mode: str) -> Dict[str, str]:
        prompt = f"{ROUTER_PROMPT}\nUser Input: {user_input}\nCurrent Mode: {current_mode}\nJSON Output:"
        
        try:
            response = self.model.generate_content(prompt)
            # Clean up response to ensure JSON
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:-3]
            return json.loads(text)
        except Exception as e:
            print(f"[Router] Error: {e}. Fallback to current mode.")
            return {"target_agent": current_mode, "reasoning": "Error in routing"}
