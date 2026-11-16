# Full stack: Robot spawn, Nav2, MoveIt 2, Vision

This guide covers the four advanced integrations on top of the basic Gazebo bridge.

---

## 1. Robot spawn

Launch:

```bash
ros2 launch prompt_to_robot_gazebo full_stack.launch.py
```

The launch file:
- Starts Gazebo (`ros_gz_sim`)
- Spawns a robot entity (`ros_gz_sim create`)
- Bridges `/cmd_vel`, `/odom`, `/clock`, `/camera`

**Customize:** point `-file` or `-topic robot_description` at your SDF/URDF
(TurtleBot4, Clearpath, custom arm+base, etc.).

---

## 2. Nav2 (closed-loop navigation)

```bash
ros2 launch prompt_to_robot_gazebo full_stack.launch.py use_nav2:=true
```

Params template: `config/nav2_params_minimal.yaml`

The `navigate` tool publishes `PoseStamped` to `/goal_pose`, which Nav2 consumes.

Checklist:
- [ ] Map / SLAM or static map loaded
- [ ] `/scan` (or depth) available for costmaps
- [ ] `base_link` / `odom` / `map` TF tree correct
- [ ] Footprint matches your robot

---

## 3. MoveIt 2 (arm)

Python:

```python
from src.backends.moveit_bridge import MockMoveItBackend, MoveItBackend

arm = MockMoveItBackend()   # develop without MoveIt
# arm = MoveItBackend()     # real moveit_py (source your moveit_config first)
```

Config notes: `config/moveit_tools.yaml`

Tool mapping:
| Tool | MoveIt role |
|------|-------------|
| `move_to` | EE pose / joint goal via move_group |
| `pick` | pre-grasp → approach → close gripper → retreat |
| `place` | move → open gripper |

Generate a MoveIt package with the Setup Assistant for your URDF, then fill in
the stubs in `MoveItBackend._move_to / _pick / _place`.

---

## 4. Vision → agent replan

```bash
python -m examples.vision_agent_demo
python -m examples.vision_agent_demo --claude
```

Components:
- `src/vision/detector.py` — `MockDetector` + `ROSCameraDetector` skeleton
- `src/backends/composite_backend.py` — routes tools + enriches `inspect`

Flow with Claude multi-turn:
1. User: "pick the red cube; if missing, pick blue"
2. Agent calls `inspect`
3. Detector returns detections in the tool_result
4. Claude chooses `object_id` from vision and calls `pick`

For real cameras, implement `ROSCameraDetector.process_image()` with YOLO or similar.

---

## Composite usage (recommended demo path)

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
result = agent.run("Inspect, then pick the red cube and place it at home")
```

When hardware/sim is ready, swap mocks:

```python
backend = CompositeBackend(
    base=GazeboROS2Backend(),
    arm=MoveItBackend(),
    detector=ROSCameraDetector("/camera/image_raw"),
)
```

---

## File map

```text
launch/full_stack.launch.py
config/nav2_params_minimal.yaml
config/moveit_tools.yaml
src/backends/moveit_bridge.py
src/backends/composite_backend.py
src/vision/detector.py
examples/vision_agent_demo.py
docs/FULL_STACK.md
```
