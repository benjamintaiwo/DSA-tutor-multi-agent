from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.sessions import InMemorySessionService
from google.adk.memory import InMemoryMemoryService
from google.genai import types
import vertexai
from vertexai import agent_engines
import os
import asyncio
import json
import logging

from tools.leetcode_mcp import LeetCodeToolMCP, LeetCodeProblemRequest
from tools.code_executor import execute_code_async
from tutor.orchestrator import TeachingOrchestrator, TeachingState
from tutor.router import IntentRouter, AgentMode

# Get API key from environment
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
APP_NAME = "agents"  # Must match the agent directory name

logger = logging.getLogger(__name__)

class TutorAgent:
    def __init__(self, project_id: str, location: str, model_name: str = "gemini-2.5-flash-lite", use_persistent_memory: bool = True):
        vertexai.init(project=project_id, location=location)
        
        # Configure Model Retry on errors
        retry_config = types.HttpRetryOptions(
            attempts=5,  # Maximum retry attempts
            exp_base=7,  # Delay multiplier
            initial_delay=1,
            http_status_codes=[429, 500, 503, 504],  # Retry on these HTTP errors
        )
        
        # Initialize Gemini Model
        if GOOGLE_API_KEY:
            self.model = Gemini(model=model_name, retry_options=retry_config, api_key=GOOGLE_API_KEY)
        else:
            self.model = Gemini(model=model_name, retry_options=retry_config, project=project_id, location=location, vertexai=True)
            
        self.orchestrator = TeachingOrchestrator()
        self.router = IntentRouter(project_id, location)
        
        # Initialize MCP-enabled LeetCode tool
        mcp_server_url = os.getenv("LEETCODE_MCP_SERVER_URL")
        self.leetcode_tool = LeetCodeToolMCP(mcp_server_url=mcp_server_url)
        
        if mcp_server_url:
            logger.info(f"Using LeetCode MCP server at {mcp_server_url}")
        else:
            logger.info(f"MCP server not configured, using direct GraphQL")
        
        # Choose between in-memory (dev/testing) or persistent (production) memory
        if use_persistent_memory:
            # VertexAiMemoryBankService provides persistent, searchable memory
            try:
                from google.adk.memory import VertexAiMemoryBankService
                self.memory_service = VertexAiMemoryBankService(
                    project_id=project_id,
                    location=location
                )
                logger.info(f"Using VertexAiMemoryBankService for persistent memory")
            except ImportError:
                logger.warning(f"VertexAiMemoryBankService not available, falling back to InMemoryMemoryService")
                self.memory_service = InMemoryMemoryService()
        else:
            self.memory_service = InMemoryMemoryService()
        
        self.session_service = InMemorySessionService()
        
        # Define async tool functions with validation
        async def fetch_leetcode_problem_async(slug: str = "", difficulty: str = "") -> str:
            """
            Fetches a LeetCode problem by its slug (e.g., 'two-sum').
            If no slug provided, returns a random problem.
            
            Args:
                slug: The problem slug (e.g., 'two-sum', 'reverse-linked-list')
                difficulty: Optional filter by difficulty ('Easy', 'Medium', 'Hard')
            
            Returns:
                JSON string with problem details (title, difficulty, description, constraints, hints)
            
            Raises:
                ValueError: If slug format is invalid
                Exception: If the problem cannot be fetched
            """
            try:
                # Validate input using Pydantic schema
                request = LeetCodeProblemRequest(
                    slug=slug if slug else None,
                    difficulty=difficulty if difficulty else None
                )
                
                # Fetch problem asynchronously
                result = await self.leetcode_tool.get_problem_async(request)
                return result
                
            except Exception as e:
                error_msg = f"Error fetching LeetCode problem: {str(e)}"
                logger.error(error_msg)
                return json.dumps({"error": error_msg})
        
        # Synchronous wrapper for the agent (ADK may not support async tools yet)
        def fetch_leetcode_problem(slug: str = "", difficulty: str = "") -> str:
            """
            Synchronous wrapper for fetch_leetcode_problem_async.
            """
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            return loop.run_until_complete(fetch_leetcode_problem_async(slug, difficulty))

        # Synchronous wrapper for code execution
        def execute_python_code(code: str) -> str:
            """
            Executes Python code in a restricted environment.
            Use this to run student's algorithms or demonstrate concepts.
            
            Args:
                code: The Python code to execute.
            
            Returns:
                JSON string with 'success', 'output', and 'error'.
            """
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            return loop.run_until_complete(execute_code_async(code))
        
        # Create the LLM Agent with tools
        self.agent = LlmAgent(
            model=self.model,
            name="ds_algorithm_tutor",
            description="An AI tutor that teaches Data Structures and Algorithms using the Socratic method.",
            instruction="""You are an expert Data Structures and Algorithms Tutor.
            Your goal is to help students solve problems using the Socratic method.
            Do NOT give the answer immediately. Guide them through questioning.
            
            Tools available:
            1. fetch_leetcode_problem: Use when the student wants to practice a specific problem or get a random one.
            2. execute_python_code: Use when the student asks to run their code or when you want to demonstrate a concept with running code.
            
            Safety: The code execution environment is restricted. Do not try to import os, sys, or access the file system.""",
            tools=[fetch_leetcode_problem, execute_python_code]
        )
        
        # Initialize Runner with app_name and agent (both required)
        from google.adk.runners import Runner
        logger.debug(f"Initializing Runner with app_name='agents'")
        self.runner = Runner(
            app_name="agents",
            agent=self.agent,
            session_service=self.session_service,
            memory_service=self.memory_service
        )
        
        # Day 4a Pattern: Initialize tracer (optional, controlled by env var)
        self.tracer = None
        self.trace_enabled = os.getenv("ENABLE_TRACE", "false").lower() == "true"

    def chat(self, user_input: str, session_id: str = "default_session", user_id: str = "student") -> str:
        # Day 4a Pattern: Initialize tracer for this session
        if self.trace_enabled:
            from evaluation.tracer import AgentTracer, EventType
            from datetime import datetime
            self.tracer = AgentTracer(session_id)
            self.tracer.log_event(EventType.SESSION_START, {
                "session_id": session_id,
                "user_id": user_id
            })
        
        # Ensure session exists (handle async calls)
        async def ensure_session():
            try:
                session = await self.session_service.get_session(session_id=session_id, user_id=user_id, app_name="agents")
                if not session:
                    raise ValueError("Session not found")
            except Exception:
                logger.debug(f"Creating new session: {session_id}")
                await self.session_service.create_session(session_id=session_id, user_id=user_id, app_name="agents")
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        loop.run_until_complete(ensure_session())
        
        # Trace: Log user input
        if self.tracer:
            self.tracer.log_event(EventType.USER_INPUT, {"input": user_input})

        # 1. Route Intent (Day 5 Pattern: Manager Agent)
        current_mode = "TUTOR"
        if self.orchestrator.student.current_state == TeachingState.INTERVIEW_MODE:
            current_mode = "INTERVIEWER"
        elif self.orchestrator.student.current_state == TeachingState.TEACHING_MODE:
            current_mode = "STUDENT"
        
        import time
        start_time = time.time()
        route_result = self.router.route(user_input, current_mode)
        routing_duration = (time.time() - start_time) * 1000
        
        target_agent = route_result.get("target_agent", "TUTOR")
        
        # Trace: Log routing decision
        if self.tracer:
            self.tracer.log_event(EventType.INTENT_ROUTING, {
                "current_mode": current_mode,
                "target_agent": target_agent,
                "reasoning": route_result.get("reasoning", "")
            }, duration_ms=routing_duration)
        
        # Update State based on Router
        old_state = self.orchestrator.student.current_state
        if target_agent == "INTERVIEWER":
            self.orchestrator.student.update_state(TeachingState.INTERVIEW_MODE)
        elif target_agent == "STUDENT":
            self.orchestrator.student.update_state(TeachingState.TEACHING_MODE)
        elif target_agent == "TUTOR" and current_mode != "TUTOR":
             self.orchestrator.student.update_state(TeachingState.GUIDANCE)
        
        # Trace: Log state transition
        if self.tracer and old_state != self.orchestrator.student.current_state:
            self.tracer.log_event(EventType.STATE_TRANSITION, {
                "from_state": old_state.value,
                "to_state": self.orchestrator.student.current_state.value
            })

        # 2. Analyze previous interaction (Adaptive Feedback)
        self.orchestrator.analyze_interaction(user_input, "")

        # 3. Orchestrator decides the next move (Directive)
        directive = self.orchestrator.determine_next_step(user_input)
        
        # 4. Update system prompt based on state and skill module
        system_prompt = self.orchestrator.get_system_prompt()
        
        # Dynamically update the agent's instruction (Persona Switching)
        self.agent.instruction = system_prompt
        
        # 5. Execute Tool if needed
        context = ""
        if directive == "FETCH_PROBLEM":
            # Trace: Log tool call
            if self.tracer:
                self.tracer.log_event(EventType.TOOL_CALL, {
                    "tool": "fetch_leetcode_problem",
                    "directive": directive
                })
            
            start_time = time.time()
            problem_data = self.leetcode_tool.get_random_problem()
            tool_duration = (time.time() - start_time) * 1000
            
            context = f"\n[System] Retrieved Problem: {problem_data}\n"
            self.orchestrator.student.current_problem = problem_data
            
            # Trace: Log tool response
            if self.tracer:
                self.tracer.log_event(EventType.TOOL_RESPONSE, {
                    "tool": "fetch_leetcode_problem",
                    "response_length": len(problem_data)
                }, duration_ms=tool_duration)

        # 6. Construct the full message for the agent
        full_message = f"{context}\nUser: {user_input}\nDirective: {directive}"
        
        # Trace: Log LLM request
        if self.tracer:
            self.tracer.log_event(EventType.LLM_REQUEST, {
                "message": full_message[:200] + "...",
                "instruction": system_prompt[:200] + "..."
            })
        
        # 7. Call the Runner with proper parameters
        from google.genai import types
        
        # Create Content object for the message
        content = types.Content(parts=[types.Part(text=full_message)])
        
        # Run the agent and collect the response
        start_time = time.time()
        events = self.runner.run(
            user_id=user_id,
            session_id=session_id,
            new_message=content
        )
        llm_duration = (time.time() - start_time) * 1000
        
        # Extract the final response from events
        response_text = ""
        for event in events:
            if hasattr(event, 'text'):
                response_text += event.text
            elif hasattr(event, 'content'):
                if hasattr(event.content, 'parts'):
                    for part in event.content.parts:
                        if hasattr(part, 'text'):
                            response_text += part.text
        
        # Trace: Log LLM response
        if self.tracer:
            self.tracer.log_event(EventType.LLM_RESPONSE, {
                "response_length": len(response_text),
                "response_preview": response_text[:200] + "..."
            }, duration_ms=llm_duration)
        
        # Trace: Log final agent response and save
        if self.tracer:
            self.tracer.log_event(EventType.AGENT_RESPONSE, {
                "response": response_text[:200] + "..." if len(response_text) > 200 else response_text
            })
            
            # Save trace to file
            from datetime import datetime
            os.makedirs("traces", exist_ok=True)
            trace_file = f"traces/{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            self.tracer.save_trace(trace_file)
            logger.debug(f"Trace saved to {trace_file}")
        
        return response_text if response_text else "No response generated"
