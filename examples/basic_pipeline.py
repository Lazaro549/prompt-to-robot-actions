"""
Basic end-to-end example of the Prompt → Plan → Execute → Evaluate pipeline.

Run from the repository root:

    python -m examples.basic_pipeline
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Allow running without installing the package
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.backends.simulator import SimulatorBackend
from src.evaluation.evaluator import Evaluator
from src.executor.executor import PlanExecutor
from src.planner.planner import Planner


def main() -> None:
    prompt = "Pick the red cube and place it on the table"

    print("=" * 60)
    print("PROMPT:", prompt)
    print("=" * 60)

    # 1. Plan
    planner = Planner(use_llm=False)  # fallback planner for now
    plan = planner.plan(prompt)

    print("\nPLAN:")
    for i, step in enumerate(plan.steps, 1):
        print(f"  {i}. {step.tool_name}({step.arguments})")
        if step.reasoning:
            print(f"     → {step.reasoning}")

    # 2. Execute
    backend = SimulatorBackend()
    executor = PlanExecutor(backend=backend, stop_on_failure=True)
    execution_result = executor.run(plan)

    print("\nEXECUTION:")
    for r in execution_result.step_results:
        status = "✓" if r.success else "✗"
        print(f"  {status} {r.step.tool_name}: {r.output.get('message') or r.error}")

    # 3. Evaluate
    evaluator = Evaluator()
    report = evaluator.evaluate(execution_result)

    print("\nEVALUATION:")
    print(f"  {report.summary}")
    print(f"  Success: {report.overall_success}")

    print("\nFINAL STATE:")
    print(json.dumps(backend.get_state(), indent=2))


if __name__ == "__main__":
    main()
