# Prompt-to-Robot-Actions

> Natural language → robot actions (Claude, Bedrock, Gazebo, Nav2, MoveIt, vision).

[![CI](https://github.com/Lazaro549/prompt-to-robot-actions/actions/workflows/ci.yml/badge.svg)](https://github.com/Lazaro549/prompt-to-robot-actions/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Pipeline:** Prompt → Plan / multi-turn Agent → validated tools → Base + Arm + Vision → logs + cost

<!-- Demo: add docs/demo.gif when recorded — see docs/DEMO.md -->

---

## Install

```bash
pip install -e ".[dev]"          # package + pytest
# or: pip install -r requirements.txt
export ANTHROPIC_API_KEY=...     # optional, for Claude
```

## CLI

```bash
ptra run "Pick the red cube and place it on the table" --backend composite
ptra run "Inspect the table" --planner claude --backend composite
ptra logs
ptra demo vision
python tools/dashboard.py        # writes logs/dashboard.html
```

## Tests

```bash
pytest -q
```

Golden prompts: `data/golden_prompts.json`

---

## Features

| Area | Status |
|------|--------|
| MIT License | ✅ |
| Installable package (`pyproject.toml`) | ✅ |
| Pytest + GitHub Actions CI | ✅ |
| CLI `ptra` | ✅ |
| Tool schema validation | ✅ |
| Recovery / retry policies | ✅ |
| Cost estimator (tokens → USD) | ✅ |
| Run log dashboard | ✅ |
| Claude / Bedrock planners | ✅ |
| Multi-turn agent | ✅ |
| Gazebo + Nav2 + MoveIt hooks | ✅ |
| Vision feedback (mock + YOLO hook) | ✅ |
| Example URDF | ✅ |

---

## Docs

- [docs/GAZEBO_ROS2.md](docs/GAZEBO_ROS2.md)
- [docs/FULL_STACK.md](docs/FULL_STACK.md)
- [docs/DEMO.md](docs/DEMO.md) — how to record a demo GIF
- [TOPICS.md](TOPICS.md) — GitHub topics + make public

---

## Author

**Lazaro Gomez Vitolo** ([Lazaro549](https://github.com/Lazaro549))  
Junior AI & Robotics Developer · Mar del Plata, Argentina
