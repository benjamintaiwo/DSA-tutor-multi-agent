# Observability & Evaluation Guide

This guide explains how to use the observability and evaluation features based on Day 4a and Day 4b patterns from the Kaggle AI Agents course.

## Day 4a: Observability (Logging & Tracing)

### Enhanced Logging

The system now uses structured logging with multiple levels:

```bash
# Standard logging (INFO level)
python main.py

# Debug logging (see full LLM prompts and state transitions)
export LOG_LEVEL=DEBUG
python main.py
```

**What you'll see in DEBUG mode:**
- Full LLM prompts (system instructions, user input, tool results)
- Detailed API responses
- Internal state transitions
- Variable values throughout execution
- Timing information for each step

### Trace Visualization

Enable tracing to capture a complete execution trace:

```bash
# Enable tracing
export ENABLE_TRACE=true
python main.py
```

**Trace files are saved to:** `traces/<session_id>_<timestamp>.json`

**Trace events captured:**
1. `SESSION_START` - Session initialization
2. `USER_INPUT` - User's message
3. `INTENT_ROUTING` - Manager agent's routing decision
4. `STATE_TRANSITION` - Agent mode changes (Tutor → Interviewer → Student)
5. `TOOL_CALL` - When fetch_leetcode_problem is invoked
6. `TOOL_RESPONSE` - Problem data returned
7. `LLM_REQUEST` - Request sent to Gemini
8. `LLM_RESPONSE` - Response from Gemini
9. `AGENT_RESPONSE` - Final response to user

**Viewing traces:**

```python
from evaluation.tracer import AgentTracer
import json

# Load trace
with open("traces/my_session_20231201_120000.json", 'r') as f:
    trace = json.load(f)

# Print formatted trace
for event in trace['events']:
    print(f"{event['timestamp']} - {event['event_type']}")
    print(f"  Duration: {event['duration_ms']}ms")
    print(f"  Data: {event['data']}\n")
```

## Day 4b: Evaluation

### Running the Evaluation Suite

The evaluation system uses structured test cases and metrics:

```bash
# Run evaluation (requires GOOGLE_API_KEY or valid GCP credentials)
python evaluation/evaluate.py
```

### Evaluation Configuration

**Config file:** `evaluation/test_config.json`

```json
{
  "metrics": [
    {
      "name": "response_match_score",
      "description": "Measures how well the agent's response matches expected behavior",
      "weight": 0.4
    },
    {
      "name": "tool_trajectory_score",
      "description": "Evaluates correct usage and sequence of tools",
      "weight": 0.3
    },
    {
      "name": "socratic_method_score",
      "description": "Measures adherence to Socratic teaching principles",
      "weight": 0.3
    }
  ]
}
```

### Test Cases

**Test cases file:** `evaluation/evalset.json`

Each test case includes:
- `expected_keywords`: Keywords that should appear in the response
- `expected_tools`: Tools that should be called
- `expected_behavior`: Expected behavior type (e.g., `socratic_hint`, `tool_usage_correct`)
- `anti_patterns`: Patterns that should NOT appear (e.g., giving away the answer)

**Example test case:**

```json
{
  "id": "hint_request_socratic",
  "name": "Hint Request (Socratic)",
  "input": "I'm stuck on this problem, can you give me a hint?",
  "expected_keywords": ["hint", "consider", "think", "what if", "try"],
  "expected_tools": [],
  "expected_behavior": "socratic_hint",
  "anti_patterns": ["here is the solution", "the answer is", "just do this"],
  "difficulty": "hard"
}
```

### Metrics Explained

1. **Response Match Score (40% weight)**
   - Checks if expected keywords are present
   - Penalizes for anti-patterns (e.g., giving direct answers when a hint is requested)
   - Range: 0.0 to 1.0

2. **Tool Trajectory Score (30% weight)**
   - Verifies correct tools were called
   - Checks tool arguments match expectations
   - Range: 0.0 to 1.0

3. **Socratic Method Score (30% weight)**
   - Measures use of questioning (e.g., "What if...", "Have you considered...")
   - Penalizes direct answers when teaching
   - Range: 0.0 to 1.0

**Overall Score:**
```
overall_score = (response_match * 0.4) + (tool_trajectory * 0.3) + (socratic_method * 0.3)
```

**Pass Threshold:** 0.7 (70%)

### Evaluation Results

Results are saved to timestamped files:

**Location:** `evaluation/results_<timestamp>.json`

**Example result:**

```json
{
  "total_tests": 7,
  "passed": 5,
  "failed": 2,
  "pass_rate": 0.71,
  "average_score": 0.78,
  "results": [
    {
      "test_case_id": "greeting_basic",
      "test_case_name": "Basic Greeting",
      "difficulty": "easy",
      "metrics": {
        "response_match_score": 0.85,
        "tool_trajectory_score": 1.0,
        "socratic_method_score": 1.0,
        "overall_score": 0.915
      },
      "passed": true
    }
  ]
}
```

### Creating Custom Test Cases

Add new test cases to `evaluation/evalset.json`:

```json
{
  "id": "your_test_id",
  "name": "Your Test Name",
  "input": "User input to test",
  "expected_keywords": ["keyword1", "keyword2"],
  "expected_tools": ["tool_name"],
  "expected_tool_args": {
    "arg_name": "expected_value"
  },
  "expected_behavior": "behavior_type",
  "anti_patterns": ["bad_pattern1"],
  "difficulty": "easy|medium|hard"
}
```

## Continuous Evaluation

For regression detection, run evaluations regularly:

```bash
# Run evaluation and save results
python evaluation/evaluate.py

# Compare with previous results
python -c "
import json
import sys

with open('evaluation/results_old.json') as f:
    old = json.load(f)
with open('evaluation/results_new.json') as f:
    new = json.load(f)

if new['average_score'] < old['average_score'] - 0.05:
    print('WARNING: Performance regression detected!')
    sys.exit(1)
"
```

## Best Practices

1. **Development:**
   - Use `DEBUG` logging to understand agent behavior
   - Enable tracing for complex debugging scenarios

2. **Testing:**
   - Run full evaluation suite before major changes
   - Add test cases for new features

3. **Production:**
   - Use `INFO` or `WARNING` log level
   - Disable tracing (performance impact)
   - Monitor evaluation metrics over time

4. **Debugging Failed Tests:**
   - Check the evaluation log file for detailed traces
   - Look for anti-patterns in the response
   - Verify expected keywords match the agent's vocabulary
   - Review tool trajectory in trace files

## Example Workflow

```bash
# 1. Development with full observability
export LOG_LEVEL=DEBUG
export ENABLE_TRACE=true
python main.py

# 2. Check traces for debugging
ls -la traces/
cat traces/default_session_20231201_120000.json

# 3. Run evaluation
python evaluation/evaluate.py

# 4. Review results
cat evaluation/results_*.json | jq '.average_score'

# 5. Fix issues, re-run evaluation
# ... make changes ...
python evaluation/evaluate.py

# 6. Compare scores
# If improved, commit changes
```
