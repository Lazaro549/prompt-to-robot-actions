"""
Full pipeline with structured JSON logging (tokens + latency).

Works with fallback planner (no API key) or Claude (with key).

Run:
    python -m examples.full_pipeline_with_logging
    python -m examples.full_pipeline_with_logging --claude
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.backends.simulator import SimulatorBackend
from src.evaluation.evaluator import Evaluator
from src.executor.executor import PlanExecutor
from src.logging.run_logger import RunLogger
from src.planner.planner import Planner


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--claude", action="store_true", help="Use Claude tool calling")
    parser.add_argument(
        "--prompt",
        default="Pick the red cube and place it on the table",
        help="Natural language prompt",
    )
    args = parser.parse_args()

    use_llm = args.claude
    if use_llm and not os.getenv("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY required for --claude")
        sys.exit(1)

    prompt = args.prompt
    planner_name = "claude" if use_llm else "fallback"
    model = "claude-sonnet-4-5" if use_llm else None

    print("=" * 60)
    print(f"PROMPT: {prompt}")
    print(f"PLANNER: {planner_name}")
    print("=" * 60)

    logger = RunLogger(prompt=prompt, planner=planner_name, model=model)

    # Plan
    t0 = time.perf_counter()
    planner = Planner(use_llm=use_llm, model=model or "claude-sonnet-4-5")
    plan = planner.plan(prompt)
    plan_ms = (time.perf_counter() - t0) * 1000

    print("\nPLAN:")
    for i, step in enumerate(plan.steps, 1):
        print(f"  {i}. {step.tool_name}({step.arguments})")

    logger.mark_plan(plan.to_dict(), latency_ms=plan_ms)

    # Execute
    t0 = time.perf_counter()
    backend = SimulatorBackend()
    executor = PlanExecutor(backend=backend)
    execution = executor.run(plan)
    exec_ms = (time.perf_counter() - t0) * 1000

    print("\nEXECUTION:")
    for r in execution.step_results:
        status = "✓" if r.success else "✗"
        print(f"  {status} {r.step.tool_name}: {r.output.get('message') or r.error}")

    logger.mark_execution(execution.to_dict(), latency_ms=exec_ms)

    # Evaluate
    report = Evaluator().evaluate(execution)
    print("\nEVALUATION:")
    print(f"  {report.summary}")

    logger.mark_evaluation(report.to_dict())
    path = logger.save()

    print(f"\nLog saved → {path}")
    print("\nFINAL STATE:")
    print(json.dumps(backend.get_state(), indent=2))


if __name__ == "__main__":
    main()
