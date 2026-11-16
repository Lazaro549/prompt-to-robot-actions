# ROS 2 + Gazebo Integration Guide

This document explains how to connect **prompt-to-robot-actions** to a Gazebo simulation through ROS 2.

---

## Architecture

```text
Natural language prompt
        ↓
Claude / Bedrock / fallback planner
        ↓
PlanExecutor
        ↓
GazeboROS2Backend  ─── rclpy node
        ↓
  /cmd_vel   /goal_pose   gripper services
        ↓
ros_gz_bridge
        ↓
Gazebo (robot model + world)
```

---

## 1. Development without Gazebo (recommended first)

```bash
python -m examples.gazebo_agent_demo
python -m examples.gazebo_agent_demo --claude
```

Uses `MockGazeboBackend` — same tool interface, pure Python.

---

## 2. Real Gazebo stack

### Prerequisites

- ROS 2 (Humble, Iron, or Jazzy)
- Gazebo Fortress or Harmonic
- Packages: `ros_gz_sim`, `ros_gz_bridge`, `geometry_msgs`, `rclpy`

### Build the helper package

```bash
cd ros2_ws
rosdep install --from-paths src -y --ignore-src   # if needed
colcon build --packages-select prompt_to_robot_gazebo
source install/setup.bash
```

### Launch simulation

```bash
ros2 launch prompt_to_robot_gazebo gazebo_sim.launch.py
```

This starts:
- Gazebo with an empty world
- Clock bridge (`/clock`)
- `/cmd_vel` bridge (ROS → Gazebo)

**Important:** spawn your own robot model and adapt topic names in:
- `src/backends/gazebo_ros2.py` → `GazeboROS2Config`
- `ros2_ws/.../config/bridge.yaml`
- the launch file bridges

### Run the agent against Gazebo

```python
from src.backends.gazebo_ros2 import GazeboROS2Backend, GazeboROS2Config
from src.agent import RobotAgent

config = GazeboROS2Config(
    cmd_vel_topic="/cmd_vel",
    goal_pose_topic="/goal_pose",
    frame_id="map",
)
backend = GazeboROS2Backend(config)
agent = RobotAgent(backend=backend)
result = agent.run("Navigate to the table and inspect the area")
backend.shutdown()
```

---

## 3. Tool → ROS mapping

| Tool | ROS / Gazebo action |
|------|---------------------|
| `navigate` | Publish `PoseStamped` on `/goal_pose` (Nav2-compatible) |
| `move_to` | Open-loop `/cmd_vel` (replace with MoveIt / arm controller for manipulators) |
| `pick` | Gripper close service/topic (stub — wire to your robot) |
| `place` | Gripper open + optional arm goal |
| `inspect` | Intended to sample `/camera/image_raw` |
| `wait` | `time.sleep` |

---

## 4. Recommended next improvements

1. **Spawn a real robot** (TurtleBot4, Clearpath, or custom URDF) in the launch file.
2. **Closed-loop navigation** with Nav2 instead of open-loop `cmd_vel`.
3. **MoveIt 2** for arm `move_to` / `pick` / `place`.
4. **Vision**: subscribe to camera topic and return detections to the agent so Claude can replan.
5. **World with named objects** so `object_id` in pick matches Gazebo model names.

---

## 5. Troubleshooting

| Symptom | Check |
|---------|--------|
| `ImportError: rclpy` | Source ROS 2 setup.bash before running Python |
| No robot motion | `ros2 topic echo /cmd_vel` and verify the Gazebo bridge topic matches the model |
| Goal ignored | Confirm Nav2 or a simple pose follower is running |
| Time issues | Ensure `/clock` is bridged and `use_sim_time:=true` |

---

## Files added for this integration

```text
src/backends/gazebo_ros2.py          # MockGazeboBackend + GazeboROS2Backend
ros2_ws/src/prompt_to_robot_gazebo/
  package.xml
  CMakeLists.txt
  launch/gazebo_sim.launch.py
  config/bridge.yaml
examples/gazebo_agent_demo.py
docs/GAZEBO_ROS2.md                  # this file
```
