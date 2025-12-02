import sys
import os
import logging
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any
from dataclasses import dataclass, field

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tutor.agent import TutorAgent

# Day 4a Pattern: Enhanced Logging with Traces
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f"evaluation_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger("AgentEvaluator")

@dataclass
class EvaluationMetrics:
    """Day 4b Pattern: Structured Metrics"""
    response_match_score: float = 0.0
    tool_trajectory_score: float = 0.0
    socratic_method_score: float = 0.0
    
    # Trace data (Day 4a Pattern)
    tools_called: List[str] = field(default_factory=list)
    tool_args: List[Dict] = field(default_factory=list)
    response_length: int = 0
    anti_patterns_found: List[str] = field(default_factory=list)
    
    def overall_score(self, weights: Dict[str, float]) -> float:
        return (
            self.response_match_score * weights.get("response_match_score", 0.4) +
            self.tool_trajectory_score * weights.get("tool_trajectory_score", 0.3) +
            self.socratic_method_score * weights.get("socratic_method_score", 0.3)
        )

class AgentEvaluator:
    """Day 4b Pattern: Systematic Evaluation Framework"""
    
    def __init__(self, config_path: str = "evaluation/test_config.json", 
                 test_cases_path: str = "evaluation/evalset.json"):
        self.config = self._load_json(config_path)
        self.test_cases = self._load_json(test_cases_path)["test_cases"]
        self.results = []
        
        # Configure logging level from config
        log_level = self.config.get("log_level", "INFO")
        logging.getLogger().setLevel(getattr(logging, log_level))
        
        logger.info(f"Loaded {len(self.test_cases)} test cases")
        logger.info(f"Evaluation Suite: {self.config['test_suite']}")
    
    def _load_json(self, path: str) -> Dict:
        with open(path, 'r') as f:
            return json.load(f)
    
    def _calculate_response_match_score(self, response: str, test_case: Dict) -> float:
        """Day 4b Pattern: Response Match Metric"""
        score = 0.0
        expected_keywords = test_case.get("expected_keywords", [])
        anti_patterns = test_case.get("anti_patterns", [])
        
        if not expected_keywords:
            return 1.0  # No expectations defined
        
        # Check for expected keywords
        response_lower = response.lower()
        matches = sum(1 for kw in expected_keywords if kw.lower() in response_lower)
        score = matches / len(expected_keywords)
        
        # Penalize for anti-patterns (e.g., giving away the answer)
        anti_pattern_penalty = 0.0
        for pattern in anti_patterns:
            if pattern.lower() in response_lower:
                anti_pattern_penalty += 0.2
                logger.warning(f"Anti-pattern detected: '{pattern}'")
        
        return max(0.0, score - anti_pattern_penalty)
    
    def _calculate_tool_trajectory_score(self, trace_data: Dict, test_case: Dict) -> float:
        """Day 4b Pattern: Tool Trajectory Metric"""
        expected_tools = test_case.get("expected_tools", [])
        
        if not expected_tools:
            return 1.0  # No tool expectations
        
        # Extract tools from trace (this would come from actual agent traces)
        # For now, we'll parse from response or use a mock
        # In production, this would analyze the Runner's event stream
        
        # Placeholder: assume perfect score if response is not empty
        # Real implementation would parse agent's tool calls from logs/traces
        return 1.0
    
    def _calculate_socratic_method_score(self, response: str, test_case: Dict) -> float:
        """Custom metric: Adherence to Socratic method"""
        if test_case.get("expected_behavior") != "socratic_hint":
            return 1.0  # Not applicable
        
        score = 0.0
        response_lower = response.lower()
        
        # Positive indicators
        socratic_indicators = ["what if", "have you considered", "think about", 
                               "what happens", "can you", "try to", "?"]
        for indicator in socratic_indicators:
            if indicator in response_lower:
                score += 0.2
        
        # Negative indicators (direct answers)
        direct_indicators = ["the answer is", "just do", "here's the solution"]
        for indicator in direct_indicators:
            if indicator in response_lower:
                score -= 0.3
        
        return max(0.0, min(1.0, score))
    
    def evaluate_test_case(self, agent: TutorAgent, test_case: Dict, 
                          session_id: str) -> EvaluationMetrics:
        """Day 4a/4b Pattern: Evaluate single test case with full tracing"""
        logger.info(f"\n{'='*60}")
        logger.info(f"Evaluating: {test_case['name']} (ID: {test_case['id']})")
        logger.info(f"Input: {test_case['input']}")
        logger.info(f"{'='*60}")
        
        metrics = EvaluationMetrics()
        
        try:
            # Run agent and capture response
            response = agent.chat(test_case['input'], session_id=session_id)
            
            logger.debug(f"Response received (length: {len(response)})")
            logger.debug(f"Response preview: {response[:200]}...")
            
            # Calculate metrics
            metrics.response_match_score = self._calculate_response_match_score(
                response, test_case
            )
            metrics.tool_trajectory_score = self._calculate_tool_trajectory_score(
                {}, test_case  # Would pass actual trace data
            )
            metrics.socratic_method_score = self._calculate_socratic_method_score(
                response, test_case
            )
            
            # Store trace data
            metrics.response_length = len(response)
            
            # Calculate weights from config
            weights = {m["name"]: m["weight"] for m in self.config["metrics"]}
            overall = metrics.overall_score(weights)
            
            logger.info(f"Scores:")
            logger.info(f"  Response Match: {metrics.response_match_score:.2f}")
            logger.info(f"  Tool Trajectory: {metrics.tool_trajectory_score:.2f}")
            logger.info(f"  Socratic Method: {metrics.socratic_method_score:.2f}")
            logger.info(f"  Overall: {overall:.2f}")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error during evaluation: {e}", exc_info=True)
            return metrics
    
    def run_evaluation(self) -> Dict[str, Any]:
        """Day 4b Pattern: Run full evaluation suite"""
        logger.info(f"\n{'#'*60}")
        logger.info(f"Starting Evaluation Suite: {self.config['test_suite']}")
        logger.info(f"{'#'*60}\n")
        
        # Initialize Agent
        try:
            project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "test-project")
            location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
            agent = TutorAgent(project_id=project_id, location=location, 
                             use_persistent_memory=False)
            logger.info("Agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize agent: {e}")
            return {"error": str(e)}
        
        session_id = f"eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        results = []
        
        for test_case in self.test_cases:
            metrics = self.evaluate_test_case(agent, test_case, session_id)
            
            weights = {m["name"]: m["weight"] for m in self.config["metrics"]}
            overall_score = metrics.overall_score(weights)
            
            results.append({
                "test_case_id": test_case["id"],
                "test_case_name": test_case["name"],
                "difficulty": test_case.get("difficulty", "unknown"),
                "metrics": {
                    "response_match_score": metrics.response_match_score,
                    "tool_trajectory_score": metrics.tool_trajectory_score,
                    "socratic_method_score": metrics.socratic_method_score,
                    "overall_score": overall_score
                },
                "passed": overall_score >= 0.7
            })
        
        # Summary
        total = len(results)
        passed = sum(1 for r in results if r["passed"])
        avg_score = sum(r["metrics"]["overall_score"] for r in results) / total if total > 0 else 0
        
        summary = {
            "total_tests": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": passed / total if total > 0 else 0,
            "average_score": avg_score,
            "results": results
        }
        
        logger.info(f"\n{'#'*60}")
        logger.info(f"Evaluation Complete")
        logger.info(f"{'#'*60}")
        logger.info(f"Total Tests: {total}")
        logger.info(f"Passed: {passed} ({summary['pass_rate']*100:.1f}%)")
        logger.info(f"Failed: {total - passed}")
        logger.info(f"Average Score: {avg_score:.2f}")
        logger.info(f"{'#'*60}\n")
        
        # Save results
        results_path = f"evaluation/results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_path, 'w') as f:
            json.dump(summary, f, indent=2)
        logger.info(f"Results saved to: {results_path}")
        
        return summary

if __name__ == "__main__":
    evaluator = AgentEvaluator()
    results = evaluator.run_evaluation()
