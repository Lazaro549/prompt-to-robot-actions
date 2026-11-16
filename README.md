# Prompt-to-Robot-Actions

> Framework that turns natural language prompts into robot actions.

**Pipeline:**  
`Prompt → Planning → Tool Calls → Execution (sim / ROS 2) → Evaluation + Logging`

Supports **Claude** (Anthropic API), **Amazon Bedrock**, a **multi-turn agent loop**, structured **JSON logging**, and a **ROS 2 backend** (mock + skeleton).

---

## Install

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...   # for Claude
# AWS credentials required for Bedrock (env / profile / IAM role)
```

---

## Quick starts

```bash
# 1. Fallback planner (no API key)
python -m examples.basic_pipeline

# 2. Claude tool calling (one-shot plan)
python -m examples.claude_pipeline

# 3. Full pipeline + structured JSON logs
python -m examples.full_pipeline_with_logging
python -m examples.full_pipeline_with_logging --claude

# 4. Multi-turn agent (Claude sees tool results and can replan)
python -m examples.agent_loop_demo
```

---

## Features

| Feature | Status | Notes |
|---------|--------|-------|
| Tool definitions | ✅ | move, pick, place, inspect, navigate, wait |
| Fallback planner | ✅ | Keyword-based, no API key |
| Claude tool calling | ✅ | `src/planner/claude_planner.py` |
| Amazon Bedrock planner | ✅ | `src/planner/bedrock_planner.py` (Converse API) |
| Multi-turn agent loop | ✅ | Claude executes → sees result → replans |
| Simulator backend | ✅ | In-memory state |
| ROS 2 backend | ✅ | `MockROS2Backend` + real skeleton |
| Structured JSON logging | ✅ | Tokens, latency, plan, execution |
| Evaluator | ✅ | Success / failure report |

---

## Architecture

```text
                    ┌── one-shot plan ─────────────────┐
User Prompt ───────┤  Claude  /  Bedrock  /  fallback   ├─── Plan
                    └── multi-turn agent loop ─────────┘
                                                      │
                                                      ▼
                                               PlanExecutor
                                                      │
                         ┌────────────────┼───────────────┐
                         ▼              ▼              ▼
                   Simulator      MockROS2Backend   ROS2Backend
                         │
                         ▼
                   Evaluator + RunLogger (JSON)
```

---

## Project structure

```text
src/
├── planner/
│   ├── planner.py           # Unified entry (fallback / claude / bedrock)
│   ├── claude_planner.py    # Anthropic tool use
│   └── bedrock_planner.py   # Bedrock Converse + toolConfig
├── agent/
│   └── agent_loop.py        # Multi-turn Claude agent
├── tools/
│   └── definitions.py
├── executor/
│   └── executor.py
├── backends/
│   ├── simulator.py
│   └── ros2_backend.py      # Mock + real skeleton
├── evaluation/
│   └── evaluator.py
└── logging/
    └── run_logger.py         # Structured JSON logs

examples/
├── basic_pipeline.py
├── claude_pipeline.py
├── full_pipeline_with_logging.py
└── agent_loop_demo.py
```

---

## Usage snippets

**One-shot Claude plan**
```python
from src.planner.planner import Planner
plan = Planner(use_llm=True, provider="claude").plan("Pick the red cube")
```

**Bedrock plan**
```python
plan = Planner(
    use_llm=True,
    provider="bedrock",
    model="anthropic.claude-3-5-sonnet-20241022-v2:0",
).plan("Pick the red cube")
```

**Multi-turn agent**
```python
from src.agent import RobotAgent
from src.backends.simulator import SimulatorBackend

agent = RobotAgent(backend=SimulatorBackend())
result = agent.run("Pick the red cube. If it fails, try blue.")
```

**ROS 2 mock**
```python
from src.backends.ros2_backend import MockROS2Backend
backend = MockROS2Backend()
```

---

## Logs

Every run that uses `RunLogger` writes a JSON file under `logs/` with:

- plan steps
- execution results
- evaluation summary
- token counts (when available)
- latency (planning / execution / total)

---

## Author

**Lazaro Gomez Vitolo** ([Lazaro549](https://github.com/Lazaro549))  
Junior AI & Robotics Developer · Mar del Plata, Argentina

Related: [aws-bedrock-robotics-demo](https://github.com/Lazaro549/aws-bedrock-robotics-demo) · [robot-vision-dashboard](https://github.com/Lazaro549/robot-vision-dashboard) · [ai-engineering-lab](https://github.com/Lazaro549/ai-engineering-lab)
