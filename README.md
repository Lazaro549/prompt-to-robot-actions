# Prompt-to-Robot-Actions

> Natural language → robot actions (Claude, Bedrock, Gazebo, Nav2, MoveIt, vision).

[![CI](https://github.com/Lazaro549/prompt-to-robot-actions/actions/workflows/ci.yml/badge.svg)](https://github.com/Lazaro549/prompt-to-robot-actions/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Version 0.3.0** — see [CHANGELOG.md](CHANGELOG.md)

<!-- Add docs/demo.gif when recorded (docs/DEMO.md) -->

---

## Install

```bash
pip install -e ".[dev]"
export ANTHROPIC_API_KEY=...   # optional
pytest -q                      # coverage + tests
```

## CLI

```bash
ptra run "Pick the red cube" --backend composite
ptra run "Pick the red cube" --dry-run
ptra run "Pick the red cube" --recovery --jsonl
ptra dashboard
ptra demo recovery
ptra logs
```

---

## Modes compared

| Mode | When to use | Replans? | Needs API |
|------|-------------|----------|-----------|
| **One-shot plan** (`Planner`) | Simple scripts, offline | No | Optional |
| **Multi-turn agent** (`RobotAgent`) | Failures, inspect-then-act | Yes | Claude |
| **Composite + vision** | Base + arm + detections | With agent | Optional |

```text
Prompt
  ├─ one-shot:  Planner → PlanExecutor → Backend
  └─ agent:     RobotAgent loop (tool_result → Claude → more tools)
                      ↓
              CompositeBackend (base | arm | vision)
                      ↓
              Safety + validation + recovery + JSONL logs + cost
```

---

## Ecosystem

```text
prompt-to-robot-actions (this repo)
  ├─ planning / agent / safety / logs
  ├─ backends: simulator, Gazebo, Nav2, MoveIt, vision
  │
  ├─ related: aws-bedrock-robotics-demo
  ├─ related: robot-vision-dashboard
  └─ related: ai-engineering-lab
```

---

## Highlights (v0.3)

- Config YAML, safety zones, JSONL stream, cost estimates
- `ptra` dry-run / recovery / dashboard
- Backend Protocol + contract tests, pytest-cov, mypy CI
- Gazebo world `table_cubes.sdf`, Nav2 stub, MoveIt pick pipeline stages
- CONTRIBUTING + issue templates

Docs: [FULL_STACK](docs/FULL_STACK.md) · [GAZEBO](docs/GAZEBO_ROS2.md) · [DEMO](docs/DEMO.md) · [TOPICS](TOPICS.md)

---

## 💸 Donations

If this project helps you, you can support it with a donation:

| | |
|---|---|
| 🇦🇷 **ARS (Argentina)** | Alias: `lazaro.503.alaba.mp` |
| 🌎 **USD** (local transfers within Argentina only) | Alias: `ahogada.duras.foca` |

Thank you!

---

## Author

**Lazaro Gomez Vitolo** ([Lazaro549](https://github.com/Lazaro549))  
Junior AI & Robotics Developer · Mar del Plata, Argentina
