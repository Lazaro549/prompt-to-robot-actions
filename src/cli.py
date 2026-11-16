"""
Unified CLI for prompt-to-robot-actions.

  ptra run "Pick the red cube" --backend composite
  ptra run "..." --dry-run
  ptra logs
  ptra dashboard
  ptra demo vision
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _build_backend(name: str):
    if name == "simulator":
        from src.backends.simulator import SimulatorBackend

        return SimulatorBackend()
    if name == "mock-gazebo":
        from src.backends.gazebo_ros2 import MockGazeboBackend

        return MockGazeboBackend()
    if name == "composite":
        from src.backends.composite_backend import CompositeBackend
        from src.backends.gazebo_ros2 import MockGazeboBackend
        from src.backends.moveit_bridge import MockMoveItBackend
        from src.vision import MockDetector

        return CompositeBackend(
            base=MockGazeboBackend(),
            arm=MockMoveItBackend(),
            detector=MockDetector(),
        )
    raise SystemExit(f"Unknown backend: {name}")


def cmd_run(args: argparse.Namespace) -> int:
    from src.cost import estimate_cost
    from src.executor.executor import PlanExecutor
    from src.executor.recovery import RecoveryPolicy
    from src.logging.jsonl_stream import JsonlStream
    from src.logging.run_logger import RunLogger
    from src.planner.planner import Planner
    from src.safety import SafetyGuard
    from src.tools.validation import validate_tool_call

    backend = _build_backend(args.backend)
    use_llm = args.planner in ("claude", "bedrock")
    provider = "bedrock" if args.planner == "bedrock" else "claude"

    logger = RunLogger(
        prompt=args.prompt,
        planner=args.planner,
        model=args.model,
        log_dir=args.log_dir,
    )
    stream = JsonlStream(Path(args.log_dir) / "events.jsonl") if args.jsonl else None
    guard = SafetyGuard()

    planner = Planner(use_llm=use_llm, provider=provider, model=args.model)
    plan = planner.plan(args.prompt)
    print("PLAN:")
    for i, s in enumerate(plan.steps, 1):
        print(f"  {i}. {s.tool_name}({s.arguments})")
        if stream:
            stream.emit("plan_step", tool=s.tool_name, arguments=s.arguments)

    logger.mark_plan(plan.to_dict(), latency_ms=0)

    if args.dry_run:
        print("\nDRY-RUN: validating tools only (no execution)")
        ok = True
        for s in plan.steps:
            try:
                validate_tool_call(s.tool_name, s.arguments)
                safe, err = guard.check(s.tool_name, s.arguments)
                if not safe:
                    print(f"  SAFETY FAIL {s.tool_name}: {err}")
                    ok = False
                else:
                    print(f"  OK {s.tool_name}")
            except Exception as exc:  # noqa: BLE001
                print(f"  INVALID {s.tool_name}: {exc}")
                ok = False
        logger.add_extra(dry_run=True)
        path = logger.save()
        print(f"Log saved: {path}")
        return 0 if ok else 1

    recovery = RecoveryPolicy() if args.recovery else None
    result = PlanExecutor(
        backend,
        stop_on_failure=not args.continue_on_fail,
        recovery=recovery,
    ).run(plan)

    print("\nEXECUTION:")
    for r in result.step_results:
        mark = "OK" if r.success else "FAIL"
        print(f"  [{mark}] {r.step.tool_name}: {r.output.get('message') or r.error}")
        if stream:
            stream.emit(
                "step_result",
                tool=r.step.tool_name,
                success=r.success,
                error=r.error,
            )

    logger.mark_execution(result.to_dict(), latency_ms=0)

    # Optional cost (0 tokens for fallback)
    cost = estimate_cost(args.model, 0, 0)
    logger.add_extra(total_cost_usd=cost.total_cost_usd)

    path = logger.save()
    print(f"\nLog saved: {path}")
    print(f"Success: {result.overall_success}")
    return 0 if result.overall_success else 1


def cmd_logs(args: argparse.Namespace) -> int:
    log_dir = Path(args.log_dir)
    if not log_dir.exists():
        print("No logs directory.")
        return 0
    files = sorted(log_dir.glob("run_*.json"))
    if not files:
        print("No run logs found.")
        return 0
    for f in files[-args.limit :]:
        data = json.loads(f.read_text())
        ok = data.get("overall_success")
        print(
            f"{f.name}  success={ok}  planner={data.get('planner')}  "
            f"prompt={data.get('prompt', '')[:50]!r}"
        )
    return 0


def cmd_dashboard(args: argparse.Namespace) -> int:
    from tools.dashboard import build_dashboard

    path = build_dashboard(Path(args.log_dir), Path(args.log_dir) / "dashboard.html")
    print(f"Dashboard: {path}")
    return 0


def cmd_demo(args: argparse.Namespace) -> int:
    if args.name == "vision":
        from examples.vision_agent_demo import main as vision_main

        sys.argv = ["vision_agent_demo"]
        vision_main()
        return 0
    if args.name == "basic":
        from examples.basic_pipeline import main as basic_main

        basic_main()
        return 0
    if args.name == "recovery":
        from examples.recovery_demo import main as recovery_main

        recovery_main()
        return 0
    print(f"Unknown demo: {args.name}")
    return 1


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="ptra", description="Prompt-to-Robot-Actions CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    run_p = sub.add_parser("run", help="Run a prompt through the pipeline")
    run_p.add_argument("prompt")
    run_p.add_argument(
        "--backend",
        default="simulator",
        choices=["simulator", "mock-gazebo", "composite"],
    )
    run_p.add_argument(
        "--planner",
        default="fallback",
        choices=["fallback", "claude", "bedrock"],
    )
    run_p.add_argument("--model", default="claude-sonnet-4-5")
    run_p.add_argument("--log-dir", default="logs")
    run_p.add_argument("--continue-on-fail", action="store_true")
    run_p.add_argument("--dry-run", action="store_true", help="Plan + validate only")
    run_p.add_argument("--recovery", action="store_true", help="Enable recovery policy")
    run_p.add_argument("--jsonl", action="store_true", help="Stream events to logs/events.jsonl")
    run_p.set_defaults(func=cmd_run)

    logs_p = sub.add_parser("logs", help="List recent run logs")
    logs_p.add_argument("--log-dir", default="logs")
    logs_p.add_argument("--limit", type=int, default=10)
    logs_p.set_defaults(func=cmd_logs)

    dash_p = sub.add_parser("dashboard", help="Build HTML dashboard from logs")
    dash_p.add_argument("--log-dir", default="logs")
    dash_p.set_defaults(func=cmd_dashboard)

    demo_p = sub.add_parser("demo", help="Run a built-in demo")
    demo_p.add_argument("name", choices=["basic", "vision", "recovery"])
    demo_p.set_defaults(func=cmd_demo)

    args = parser.parse_args(argv)
    raise SystemExit(args.func(args))


if __name__ == "__main__":
    main()
