"""
Day 4a Pattern: Trace Visualization

This module provides utilities to visualize agent traces, showing:
- LLM prompts and responses
- Tool calls and their arguments
- State transitions
- Timing information
"""

import json
from datetime import datetime
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
from enum import Enum

class EventType(Enum):
    """Types of events in an agent trace"""
    SESSION_START = "session_start"
    USER_INPUT = "user_input"
    INTENT_ROUTING = "intent_routing"
    STATE_TRANSITION = "state_transition"
    TOOL_CALL = "tool_call"
    TOOL_RESPONSE = "tool_response"
    LLM_REQUEST = "llm_request"
    LLM_RESPONSE = "llm_response"
    AGENT_RESPONSE = "agent_response"
    ERROR = "error"

@dataclass
class TraceEvent:
    """A single event in the agent execution trace"""
    timestamp: str
    event_type: EventType
    data: Dict[str, Any]
    duration_ms: float = 0.0
    
    def to_dict(self):
        return {
            "timestamp": self.timestamp,
            "event_type": self.event_type.value,
            "data": self.data,
            "duration_ms": self.duration_ms
        }

class AgentTracer:
    """
    Day 4a Pattern: Captures and visualizes agent execution traces
    
    Usage:
        tracer = AgentTracer()
        tracer.log_event(EventType.USER_INPUT, {"input": "Give me a problem"})
        tracer.log_event(EventType.TOOL_CALL, {"tool": "fetch_leetcode_problem", "args": {}})
        tracer.save_trace("trace.json")
    """
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.events: List[TraceEvent] = []
        self.start_time = datetime.now()
    
    def log_event(self, event_type: EventType, data: Dict[str, Any], duration_ms: float = 0.0):
        """Log a single event in the trace"""
        event = TraceEvent(
            timestamp=datetime.now().isoformat(),
            event_type=event_type,
            data=data,
            duration_ms=duration_ms
        )
        self.events.append(event)
    
    def get_trace(self) -> List[Dict]:
        """Get the full trace as a list of dictionaries"""
        return [event.to_dict() for event in self.events]
    
    def save_trace(self, filepath: str):
        """Save trace to JSON file"""
        trace_data = {
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat(),
            "duration_ms": (datetime.now() - self.start_time).total_seconds() * 1000,
            "events": self.get_trace()
        }
        
        with open(filepath, 'w') as f:
            json.dump(trace_data, f, indent=2)
    
    def print_trace(self):
        """Print a human-readable trace visualization"""
        print("\n" + "="*80)
        print(f"AGENT TRACE - Session: {self.session_id}")
        print("="*80)
        
        for i, event in enumerate(self.events, 1):
            print(f"\n[{i}] {event.timestamp}")
            print(f"    Type: {event.event_type.value}")
            
            if event.duration_ms > 0:
                print(f"    Duration: {event.duration_ms:.2f}ms")
            
            print(f"    Data:")
            for key, value in event.data.items():
                # Truncate long values
                value_str = str(value)
                if len(value_str) > 100:
                    value_str = value_str[:100] + "..."
                print(f"      {key}: {value_str}")
        
        print("\n" + "="*80)
        total_duration = (datetime.now() - self.start_time).total_seconds() * 1000
        print(f"Total Duration: {total_duration:.2f}ms")
        print("="*80 + "\n")

# Example usage in tutor/agent.py:
"""
# In TutorAgent.__init__:
self.tracer = None

# In TutorAgent.chat:
def chat(self, user_input: str, session_id: str = "default_session", user_id: str = "student") -> str:
    # Initialize tracer
    if os.getenv("ENABLE_TRACE", "false").lower() == "true":
        from evaluation.tracer import AgentTracer, EventType
        self.tracer = AgentTracer(session_id)
        self.tracer.log_event(EventType.SESSION_START, {"session_id": session_id, "user_id": user_id})
    
    # Log user input
    if self.tracer:
        self.tracer.log_event(EventType.USER_INPUT, {"input": user_input})
    
    # ... routing logic ...
    if self.tracer:
        self.tracer.log_event(EventType.INTENT_ROUTING, {
            "current_mode": current_mode,
            "target_agent": target_agent,
            "reasoning": route_result.get("reasoning", "")
        })
    
    # ... at the end ...
    if self.tracer:
        self.tracer.log_event(EventType.AGENT_RESPONSE, {"response": response_text[:200]})
        self.tracer.save_trace(f"traces/{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
"""
