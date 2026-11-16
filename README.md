# Prompt-to-Robot-Actions

> A clean framework that turns natural language prompts into robot actions.

**Pipeline:**  
`Prompt → Planning → Tool Calls → Execution (simulated or real) → Success Evaluation`

This repository is a practical learning and experimentation space for connecting Large Language Models (Claude / Amazon Bedrock) with robotic systems (simulated or physical).

---

## Quick Start

```bash
# From the repository root
python -m examples.basic_pipeline
```

Example output:

```text
PROMPT: Pick the red cube and place it on the table

PLAN:
  1. pick({'object_id': 'red_cube', 'force': 0.6})
  2. place({'x': 0.4, 'y': 0.0, 'z': 0.1})

EXECUTION:
  ✓ pick: Picked red_cube
  ✓ place: Placed red_cube at (0.4, 0.0, 0.1)

EVALUATION:
  Plan succeeded (2/2 steps).
```

---

## Current Status

| Component              | Status                          |
|------------------------|---------------------------------|
| Project structure      | ✅ Done                         |
| Tool definitions       | ✅ Basic set (move, pick, place, inspect, navigate, wait) |
| Fallback planner       | ✅ Keyword-based (for testing)  |
| Simulator backend      | ✅ Working                      |
| Plan executor          | ✅ Working                      |
| Evaluator              | ✅ Basic success/failure report |
| LLM planner (Claude/Bedrock) | ⏳ Next                       |
| ROS 2 backend          | ⏳ Planned                      |
| Cost & latency tracking| ⏳ Planned                      |

---

## Architecture

```text
User Prompt
    ↓
Planner (currently fallback, LLM coming next)
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
├── examples/
│   └── basic_pipeline.py      # End-to-end runnable example
├── src/
│   ├── planner/
│   │   └── planner.py         # Planner + Plan / PlanStep
│   ├── tools/
│   │   └── definitions.py     # ROBOT_TOOLS schemas
│   ├── executor/
│   │   └── executor.py        # PlanExecutor
│   ├── backends/
│   │   └── simulator.py       # In-memory robot simulator
│   └── evaluation/
│       └── evaluator.py       # EvaluationReport
└── .gitignore
```

---

## Next Steps (suggested order)

1. Replace the fallback planner with real Claude / Bedrock tool calling
2. Add more realistic failure cases and recovery logic
3. Add structured logging (JSON) of every plan + execution
4. Create a ROS 2 backend adapter
5. Track token usage and latency when using Bedrock

---

## Author

**Lazaro Gomez Vitolo** ([Lazaro549](https://github.com/Lazaro549))  
Junior AI & Robotics Developer  
Mar del Plata, Buenos Aires, Argentina

Related projects:
- [aws-bedrock-robotics-demo](https://github.com/Lazaro549/aws-bedrock-robotics-demo)
- [robot-vision-dashboard](https://github.com/Lazaro549/robot-vision-dashboard)
- [ai-engineering-lab](https://github.com/Lazaro549/ai-engineering-lab)
