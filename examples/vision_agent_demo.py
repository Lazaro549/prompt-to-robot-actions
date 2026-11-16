"""
Vision-informed agent demo.

Flow:
  1. Agent is told to pick an object
  2. It can call inspect first
  3. MockDetector returns detections
  4. With --claude, Claude sees tool results and can choose object_id from vision

Without --claude uses the one-shot fallback planner + composite backend.

Run:
    python -m examples.vision_agent_demo
    python -m examples.vision_agent_demo --claude
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.backends.composite_backend import CompositeBackend
from src.backends.gazebo_ros2 import MockGazeboBackend
from src.backends.moveit_bridge import MockMoveItBackend
from src.executor.executor import PlanExecutor
from src.logging.run_logger import RunLogger
from src.planner.planner import Planner
from src.vision import MockDetector


def run_oneshot(prompt: str, use_claude: bool) -> None:
    detector = MockDetector()
    backend = CompositeBackend(
        base=MockGazeboBackend(),
        arm=MockMoveItBackend(),
        detector=detector,
    )

    logger = RunLogger(
        prompt=prompt,
        planner="claude" if use_claude else "fallback",
        model="claude-sonnet-4-5" if use_claude else None,
    )

    planner = Planner(use_llm=use_claude)
    plan = planner.plan(prompt)
    print("\nPLAN:")
    for i, s in enumerate(plan.steps, 1):
        print(f"  {i}. {s.tool_name}({s.arguments})")

    logger.mark_plan(plan.to_dict(), latency_ms=0)
    result = PlanExecutor(backend).run(plan)

    print("\nEXECUTION:")
    for r in result.step_results:
        status = "✓" if r.success else "✗"
        print(f"  {status} {r.step.tool_name}: {r.output.get('message') or r.error}")

    logger.mark_execution(result.to_dict(), latency_ms=0)
    path = logger.save()
    print("\nSTATE:")
    print(json.dumps(backend.get_state(), indent=2))
    print(f"\nLog → {path}")


def run_agent(prompt: str) -> None:
    from src.agent import RobotAgent

    detector = MockDetector()
    backend = CompositeBackend(
        base=MockGazeboBackend(),
        arm=MockMoveItBackend(),
        detector=detector,
    )
    agent = RobotAgent(backend=backend, max_turns=8)
    result = agent.run(prompt)

    print("\nEXECUTED STEPS:")
    for step in result.executed_steps:
        ok = step["result"].get("success")
        print(f"  {'✓' if ok else '✗'} {step['tool_name']}: {step['result'].get('message') or step['result'].get('error')}")

    print(f"\nSuccess={result.final_success} tokens_in={result.total_input_tokens} "
          f"tokens_out={result.total_output_tokens} latency_ms={result.total_latency_ms}")
    print("\nSTATE:")
    print(json.dumps(backend.get_state(), indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--claude", action="store_true", help="Use Claude agent loop")
    parser.add_argument(
        "--prompt",
        default=(
            "Inspect the area, then pick the red cube and place it at coordinates "
            "0.0, 0.0, 0.1. If the red cube is not visible, pick the blue cube instead."
        ),
    )
    args = parser.parse_args()

    print("=" * 60)
    print("PROMPT:", args.prompt)
    print("=" * 60)

    # Always show what vision currently sees
    det = MockDetector().detect()
    print("\nVISION (initial):", det.summary_for_llm())

    if args.claude:
        if not os.getenv("ANTHROPIC_API_KEY"):
            print("Set ANTHROPIC_API_KEY for --claude")
            sys.exit(1)
        run_agent(args.prompt)
    else:
        run_oneshot(args.prompt, use_claude=False)


if __name__ == "__main__":
    main()
