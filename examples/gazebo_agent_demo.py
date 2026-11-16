"""
Demo: prompt → plan/agent → MockGazeboBackend (no ROS/Gazebo required).

For the real Gazebo stack:
  1. Launch simulation:  ros2 launch prompt_to_robot_gazebo gazebo_sim.launch.py
  2. Swap MockGazeboBackend for GazeboROS2Backend in this script.
  3. Run with ANTHROPIC_API_KEY set.

Run (mock):
    python -m examples.gazebo_agent_demo
    python -m examples.gazebo_agent_demo --claude
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.backends.gazebo_ros2 import MockGazeboBackend
from src.executor.executor import PlanExecutor
from src.logging.run_logger import RunLogger
from src.planner.planner import Planner


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--claude", action="store_true")
    parser.add_argument(
        "--prompt",
        default="Navigate to the table, pick the red cube, and place it at home",
    )
    args = parser.parse_args()

    if args.claude and not os.getenv("ANTHROPIC_API_KEY"):
        print("Set ANTHROPIC_API_KEY or omit --claude")
        sys.exit(1)

    prompt = args.prompt
    print("=" * 60)
    print("PROMPT:", prompt)
    print("BACKEND: MockGazeboBackend")
    print("=" * 60)

    logger = RunLogger(
        prompt=prompt,
        planner="claude" if args.claude else "fallback",
        model="claude-sonnet-4-5" if args.claude else None,
    )

    planner = Planner(use_llm=args.claude)
    plan = planner.plan(prompt)

    print("\nPLAN:")
    for i, step in enumerate(plan.steps, 1):
        print(f"  {i}. {step.tool_name}({step.arguments})")

    logger.mark_plan(plan.to_dict(), latency_ms=0)

    backend = MockGazeboBackend()
    result = PlanExecutor(backend).run(plan)

    print("\nEXECUTION:")
    for r in result.step_results:
        status = "✓" if r.success else "✗"
        print(f"  {status} {r.step.tool_name}: {r.output.get('message') or r.error}")

    logger.mark_execution(result.to_dict(), latency_ms=0)
    path = logger.save()

    print("\nGAZEBO STATE:")
    print(json.dumps(backend.get_state(), indent=2))
    print(f"\nLog → {path}")
    print("\nTo use real Gazebo:")
    print("  1. ros2 launch prompt_to_robot_gazebo gazebo_sim.launch.py")
    print("  2. Replace MockGazeboBackend with GazeboROS2Backend in this script")


if __name__ == "__main__":
    main()
