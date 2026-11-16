# Prompt-to-Robot-Actions

> Natural language → robot actions (sim, Gazebo, Nav2, MoveIt, vision).

**Pipeline:** Prompt → Plan / multi-turn Agent → Tools → Base + Arm + Vision → Logs

---

## Quick starts

```bash
pip install -r requirements.txt

python -m examples.basic_pipeline
python -m examples.claude_pipeline          # needs ANTHROPIC_API_KEY
python -m examples.agent_loop_demo
python -m examples.gazebo_agent_demo
python -m examples.vision_agent_demo         # base + arm + vision (mock)
python -m examples.vision_agent_demo --claude
```

---

## Features

| Area | Status |
|------|--------|
| Claude / Bedrock tool calling | ✅ |
| Multi-turn agent (replan on tool results) | ✅ |
| Structured JSON logs (tokens, latency) | ✅ |
| Gazebo ROS 2 backend | ✅ |
| **Robot spawn launch** | ✅ `full_stack.launch.py` |
| **Nav2 closed-loop nav** | ✅ params + launch flag |
| **MoveIt 2 arm bridge** | ✅ mock + skeleton |
| **Vision → agent feedback** | ✅ MockDetector + composite backend |

---

## Full robotics stack

Guides:
- [docs/GAZEBO_ROS2.md](docs/GAZEBO_ROS2.md) — basic Gazebo bridge
- [docs/FULL_STACK.md](docs/FULL_STACK.md) — **spawn, Nav2, MoveIt, vision**

```bash
# Gazebo + spawn + bridges (+ optional Nav2)
ros2 launch prompt_to_robot_gazebo full_stack.launch.py
ros2 launch prompt_to_robot_gazebo full_stack.launch.py use_nav2:=true
```

```python
from src.backends.composite_backend import CompositeBackend
from src.backends.gazebo_ros2 import MockGazeboBackend
from src.backends.moveit_bridge import MockMoveItBackend
from src.vision import MockDetector
from src.agent import RobotAgent

backend = CompositeBackend(
    base=MockGazeboBackend(),
    arm=MockMoveItBackend(),
    detector=MockDetector(),
)
agent = RobotAgent(backend=backend)
agent.run("Inspect the area, pick the red cube, place it at home")
```

Swap mocks for `GazeboROS2Backend`, `MoveItBackend`, `ROSCameraDetector` when the sim stack is up.

---

## Author

**Lazaro Gomez Vitolo** ([Lazaro549](https://github.com/Lazaro549))  
Junior AI & Robotics Developer · Mar del Plata, Argentina
