# Prompt-to-Robot-Actions

> A clean framework that turns natural language prompts into robot actions.

**Pipeline:**  
`Prompt → Planning → Tool Calls → Execution (simulated or real) → Success Evaluation`

This repository is a practical learning and experimentation space for connecting Large Language Models (Claude / Amazon Bedrock) with robotic systems (simulated or physical).

---

## Quick Start (fallback planner — no API key)

```bash
python -m examples.basic_pipeline
```

## Quick Start with Claude tool calling

```bash
pip install anthropic
export ANTHROPIC_API_KEY=sk-ant-...

python -m examples.claude_pipeline
```

Claude will receive the robot tool schemas and return a sequence of `tool_use` blocks that become the plan.

---

## How Claude Tool Calling Works Here

1. We send the user prompt + the `ROBOT_TOOLS` schemas to Claude.
2. Claude responds with one or more `tool_use` blocks (e.g. `pick`, `place`).
3. We convert those blocks into `PlanStep` objects.
4. The `PlanExecutor` runs the steps against the simulator (or later ROS 2).
5. The `Evaluator` reports success / failure.

Important design choice: **Claude only plans**. It does not execute the tools itself. Execution is handled by our own code so we keep full control and can swap backends.

---

## Current Status

| Component                    | Status                                      |
|------------------------------|---------------------------------------------|
| Project structure            | ✅ Done                                     |
| Tool definitions             | ✅ move, pick, place, inspect, navigate, wait |
| Fallback planner             | ✅ Keyword-based                            |
| **Claude tool-calling planner** | ✅ Working                               |
| Simulator backend            | ✅ Working                                  |
| Plan executor                | ✅ Working                                  |
| Evaluator                    | ✅ Basic success/failure report             |
| ROS 2 backend                | ⏳ Planned                                  |
| Cost & latency tracking      | ⏳ Planned                                  |

---

## Architecture

```text
User Prompt
    ↓
Planner  ───  use_llm=False → fallback
         └──  use_llm=True  → Claude tool calling
    ↓
Structured Plan (list of PlanStep)
    ↓
PlanExecutor
    ↓
Robot Backend (SimulatorBackend for now)
    ↓
Evaluator → EvaluationReport
```

---

## Project Structure

```text
prompt-to-robot-actions/
├── README.md
├── requirements.txt
├── examples/
│   ├── basic_pipeline.py       # Fallback planner
│   └── claude_pipeline.py      # Claude tool calling
├── src/
│   ├── planner/
│   │   ├── planner.py          # Main Planner + Plan / PlanStep
│   │   └── claude_planner.py   # Claude implementation
│   ├── tools/
│   │   └── definitions.py      # ROBOT_TOOLS schemas
│   ├── executor/
│   │   └── executor.py
│   ├── backends/
│   │   └── simulator.py
│   └── evaluation/
│       └── evaluator.py
└── .gitignore
```

---

## Next Steps (suggested)

1. Add structured JSON logging of every plan + execution
2. Track token usage and latency from Claude
3. Create a ROS 2 backend adapter
4. Add recovery logic when a step fails
5. Optional: multi-turn agent loop (Claude sees tool results and can replan)

---

## Author

**Lazaro Gomez Vitolo** ([Lazaro549](https://github.com/Lazaro549))  
Junior AI & Robotics Developer  
Mar del Plata, Buenos Aires, Argentina

Related projects:
- [aws-bedrock-robotics-demo](https://github.com/Lazaro549/aws-bedrock-robotics-demo)
- [robot-vision-dashboard](https://github.com/Lazaro549/robot-vision-dashboard)
- [ai-engineering-lab](https://github.com/Lazaro549/ai-engineering-lab)
