# Prompt-to-Robot-Actions

> Framework that turns natural language prompts into robot actions.

**Pipeline:**  
`Prompt → Planning → Tool Calls → Execution (sim / ROS 2 / Gazebo) → Evaluation + Logging`

Supports **Claude**, **Amazon Bedrock**, a **multi-turn agent loop**, structured **JSON logging**, and **ROS 2 + Gazebo** backends.

---

## Install

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...   # for Claude
# AWS credentials required for Bedrock
```

---

## Quick starts

```bash
# Fallback (no API key)
python -m examples.basic_pipeline

# Claude one-shot plan
python -m examples.claude_pipeline

# Full pipeline + JSON logs
python -m examples.full_pipeline_with_logging --claude

# Multi-turn agent
python -m examples.agent_loop_demo

# Gazebo-oriented demo (mock, no ROS needed)
python -m examples.gazebo_agent_demo
python -m examples.gazebo_agent_demo --claude
```

---

## Features

| Feature | Status | Notes |
|---------|--------|-------|
| Tool definitions | ✅ | move, pick, place, inspect, navigate, wait |
| Fallback / Claude / Bedrock planners | ✅ | |
| Multi-turn agent loop | ✅ | Replans from tool results |
| Simulator backend | ✅ | In-memory |
| ROS 2 backend | ✅ | Mock + skeleton |
| **Gazebo + ROS 2 backend** | ✅ | Mock + real `GazeboROS2Backend` |
| Structured JSON logging | ✅ | Tokens + latency |
| ROS 2 launch package | ✅ | `ros2_ws/src/prompt_to_robot_gazebo` |

---

## ROS 2 + Gazebo

Full guide: **[docs/GAZEBO_ROS2.md](docs/GAZEBO_ROS2.md)**

**Without Gazebo (develop first):**
```bash
python -m examples.gazebo_agent_demo
```

**With Gazebo:**
```bash
# Terminal 1 — simulation
cd ros2_ws && colcon build --packages-select prompt_to_robot_gazebo
source install/setup.bash
ros2 launch prompt_to_robot_gazebo gazebo_sim.launch.py

# Terminal 2 — agent (after sourcing ROS 2)
# Use GazeboROS2Backend instead of MockGazeboBackend
```

Tool mapping:
- `navigate` → `/goal_pose` (Nav2-compatible)
- `move_to` → `/cmd_vel` (open-loop; swap for MoveIt on arms)
- `pick` / `place` → gripper stubs (wire to your robot)
- `inspect` → camera topic (optional)

---

## Architecture

```text
Prompt → Planner (Claude | Bedrock | fallback) or multi-turn Agent
                ↓
          PlanExecutor
                ↓
    Simulator | MockGazebo | GazeboROS2 | ROS2Backend
                ↓
       Evaluator + RunLogger (JSON)
```

---

## Project structure (high level)

```text
src/backends/
  simulator.py
  ros2_backend.py
  gazebo_ros2.py          # MockGazeboBackend + GazeboROS2Backend

ros2_ws/src/prompt_to_robot_gazebo/
  launch/gazebo_sim.launch.py
  config/bridge.yaml

examples/gazebo_agent_demo.py
docs/GAZEBO_ROS2.md
```

---

## Author

**Lazaro Gomez Vitolo** ([Lazaro549](https://github.com/Lazaro549))  
Junior AI & Robotics Developer · Mar del Plata, Argentina
