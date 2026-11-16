# Prompt-to-Robot-Actions

> A clean framework that turns natural language prompts into robot actions.

**Pipeline:**  
`Prompt → Planning → Tool Calls → Execution (simulated or real) → Success Evaluation`

This repository is designed as a practical learning and experimentation space for connecting Large Language Models (Claude / Amazon Bedrock) with robotic systems (simulated or physical).

---

## Goals

- Convert natural language instructions into structured robot plans
- Use tool calling / function calling to map high-level goals to low-level actions
- Support both **simulated** and **real** robot backends
- Evaluate whether the plan succeeded (success rate, recovery, safety constraints)
- Keep the architecture simple, readable and measurable

---

## High-level Architecture

```text
User Prompt
    ↓
Planner (LLM)
    ↓
Structured Plan (JSON / sequence of tools)
    ↓
Tool Executor
    ↓
Robot Backend (Simulator | Real Hardware | ROS 2)
    ↓
Evaluation & Logging
```

---

## Planned Features

- [x] Project structure & documentation
- [ ] Prompt → structured plan (using Claude / Bedrock)
- [ ] Tool definitions for common robot actions (move, pick, place, inspect, navigate…)
- [ ] Simple simulator backend
- [ ] Evaluation metrics (success, partial success, failure reason)
- [ ] Logging of plans, tool calls and outcomes
- [ ] Optional ROS 2 bridge
- [ ] Cost & latency tracking (especially for Bedrock)

---

## Project Structure (initial)

```text
prompt-to-robot-actions/
├── README.md
├── src/
│   ├── planner/          # LLM planning logic
│   ├── tools/            # Tool definitions
│   ├── executor/         # Executes the plan
│   ├── backends/         # Simulator / ROS / hardware adapters
│   └── evaluation/       # Success metrics & logging
├── examples/
├── tests/
└── docs/
```

---

## Tech Stack (intended)

- **Language:** Python 3.11+
- **LLM:** Anthropic Claude / Amazon Bedrock
- **Robot interface:** Custom simulator first, then ROS 2
- **Evaluation:** Simple structured logs + success criteria
- **Optional:** FastAPI for a small control API

---

## Status

**Private learning repository** — early stage.  
Focused on clean architecture and measurable experiments rather than production readiness.

---

## Author

**Lazaro Gomez Vitolo** ([Lazaro549](https://github.com/Lazaro549))  
Junior AI & Robotics Developer  
Mar del Plata, Buenos Aires, Argentina

Related projects:
- [aws-bedrock-robotics-demo](https://github.com/Lazaro549/aws-bedrock-robotics-demo)
- [robot-vision-dashboard](https://github.com/Lazaro549/robot-vision-dashboard)
- [ai-engineering-lab](https://github.com/Lazaro549/ai-engineering-lab)
