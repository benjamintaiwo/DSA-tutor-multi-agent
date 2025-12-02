from enum import Enum
from typing import List, Dict, Any, Optional

from tutor.prompts import TUTOR_PROMPT, INTERVIEWER_PROMPT, STUDENT_SIM_PROMPT

class TeachingState(Enum):
    INTAKE = "INTAKE"
    ASSESSMENT = "ASSESSMENT"
    GUIDANCE = "GUIDANCE"
    FEEDBACK = "FEEDBACK"
    COMPLETED = "COMPLETED"
    INTERVIEW_MODE = "INTERVIEW_MODE"
    TEACHING_MODE = "TEACHING_MODE"

class SkillModule(Enum):
    GENERAL = "General Guidance"
    PATTERN_RECOGNITION = "Pattern Recognition"
    CONSTRAINT_ANALYSIS = "Constraint Analysis"
    EXAMPLE_SIMULATION = "Example Simulation"
    CODING_GUIDANCE = "Coding Guidance"
    META_REASONING = "Meta Reasoning"

class StudentProfile:
    def __init__(self):
        self.history: List[Dict[str, Any]] = []
        self.weaknesses: Dict[str, int] = {} # Map weakness to count
        self.strengths: List[str] = []
        self.current_problem: str = None
        self.current_state: TeachingState = TeachingState.INTAKE
        self.mastery_levels: Dict[str, float] = {skill.value: 0.5 for skill in SkillModule}

    def add_interaction(self, role: str, content: str):
        self.history.append({"role": role, "content": content})

    def record_weakness(self, weakness: str):
        self.weaknesses[weakness] = self.weaknesses.get(weakness, 0) + 1

    def update_state(self, new_state: TeachingState):
        self.current_state = new_state

class TeachingOrchestrator:
    def __init__(self):
        self.student = StudentProfile()
        self.current_skill: SkillModule = SkillModule.GENERAL

    def analyze_interaction(self, user_input: str, last_agent_response: str):
        """
        Analyzes the interaction to update student profile.
        In a real system, this would use a separate LLM call to classify the student's response.
        Here we use heuristics.
        """
        # Heuristic: Confusion about constraints
        if "constraint" in user_input.lower() or "limit" in user_input.lower():
            if "?" in user_input:
                self.student.record_weakness("Constraint Analysis")
        
        # Heuristic: Struggling with examples
        if "example" in user_input.lower() and "don't understand" in user_input.lower():
            self.student.record_weakness("Example Simulation")

        # Heuristic: Short, confused answers
        if len(user_input.split()) < 4 and "?" in user_input:
            self.student.record_weakness("Articulation")

    def determine_next_step(self, user_input: str) -> str:
        """
        Determines the next pedagogical move and Skill Module.
        """
        # Global Mode Switching
        if "interview me" in user_input.lower():
            self.student.update_state(TeachingState.INTERVIEW_MODE)
            return "SWITCH_TO_INTERVIEWER"
        
        if "i want to teach" in user_input.lower() or "student simulator" in user_input.lower():
            self.student.update_state(TeachingState.TEACHING_MODE)
            return "SWITCH_TO_STUDENT"
            
        if "help" in user_input.lower() and (self.student.current_state == TeachingState.INTERVIEW_MODE or self.student.current_state == TeachingState.TEACHING_MODE):
            self.student.update_state(TeachingState.GUIDANCE)
            return "SWITCH_TO_TUTOR"

        state = self.student.current_state
        
        # 1. State Transitions
        if state == TeachingState.INTAKE:
            if "start" in user_input.lower() or "problem" in user_input.lower():
                self.student.update_state(TeachingState.ASSESSMENT)
                return "FETCH_PROBLEM"
            return "GREETING"
        
        elif state == TeachingState.ASSESSMENT:
            if "?" in user_input:
                self.current_skill = SkillModule.CONSTRAINT_ANALYSIS
                return "CLARIFY_CONSTRAINT"
            self.student.update_state(TeachingState.GUIDANCE)
            self.current_skill = SkillModule.PATTERN_RECOGNITION
            return "ASK_APPROACH"

        elif state == TeachingState.GUIDANCE:
            # Adaptive Logic: Switch skill based on weakness
            if self.student.weaknesses.get("Constraint Analysis", 0) > 2:
                self.current_skill = SkillModule.CONSTRAINT_ANALYSIS
            elif self.student.weaknesses.get("Example Simulation", 0) > 2:
                self.current_skill = SkillModule.EXAMPLE_SIMULATION
            else:
                self.current_skill = SkillModule.CODING_GUIDANCE

            if "hint" in user_input.lower():
                return "GIVE_HINT"
            
            return "VALIDATE_AND_CHALLENGE"
            
        elif state == TeachingState.INTERVIEW_MODE:
            return "INTERVIEW_INTERACTION"
            
        elif state == TeachingState.TEACHING_MODE:
            return "STUDENT_SIMULATION"

        return "CONTINUE"

    def get_system_prompt(self) -> str:
        """
        Generates the system prompt based on State and active Skill Module.
        """
        state = self.student.current_state
        
        if state == TeachingState.INTERVIEW_MODE:
            return INTERVIEWER_PROMPT
        
        if state == TeachingState.TEACHING_MODE:
            return STUDENT_SIM_PROMPT
            
        # Standard Tutor Logic
        base_prompt = TUTOR_PROMPT
        
        skill_prompts = {
            SkillModule.GENERAL: "Focus on general guidance.",
            SkillModule.PATTERN_RECOGNITION: "Focus on helping the student identify the underlying pattern (e.g., Sliding Window, Two Pointers). Ask: 'What does this remind you of?'",
            SkillModule.CONSTRAINT_ANALYSIS: "Focus on the constraints. Ask: 'How does the input size affect your choice of algorithm? O(n) vs O(n^2)?'",
            SkillModule.EXAMPLE_SIMULATION: "Walk through the examples step-by-step. Ask the user to trace the input manually.",
            SkillModule.CODING_GUIDANCE: "Help the user structure their code. Focus on function signatures and edge cases.",
            SkillModule.META_REASONING: "Ask the user to explain *why* they chose this approach. Challenge their assumptions."
        }
        
        skill_instruction = skill_prompts.get(self.current_skill, "")
        
        return f"{base_prompt}\n\nCurrent Phase: {self.student.current_state.value}\nActive Skill Module: {self.current_skill.value}\nInstruction: {skill_instruction}"
