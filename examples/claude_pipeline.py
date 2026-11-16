"""
End-to-end example using Claude tool calling for planning.

Requirements:
    pip install anthropic
    export ANTHROPIC_API_KEY=sk-ant-...

Run from the repository root:

    python -m examples.claude_pipeline
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.backends.simulator import SimulatorBackend
from src.evaluation.evaluator import Evaluator
from src.executor.executor import PlanExecutor
from src.planner.planner import Planner


def main() -> None:
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable is not set.")
        print("Set it with: export ANTHROPIC_API_KEY=sk-ant-...")
        sys.exit(1)

    prompt = "Pick the red cube and carefully place it on the table at coordinates 0.5, 0.1, 0.05"

    print("=" * 60)
    print("PROMPT:", prompt)
    print("=" * 60)

    # 1. Plan with Claude tool calling
    planner = Planner(model="claude-sonnet-4-5", use_llm=True)
    plan = planner.plan(prompt)

    print("\nPLAN (from Claude):")
    for i, step in enumerate(plan.steps, 1):
        print(f"  {i}. {step.tool_name}({step.arguments})")

    if plan.raw_llm_response:
        print("\nRaw LLM response snippet:")
        print(f"  {plan.raw_llm_response[:200]}...")

    # 2. Execute on simulator
    backend = SimulatorBackend()
    executor = PlanExecutor(backend=backend, stop_on_failure=True)
    execution_result = executor.run(plan)

    print("\nEXECUTION:")
    for r in execution_result.step_results:
        status = "✓" if r.success else "✗"
        msg = r.output.get("message") or r.error
        print(f"  {status} {r.step.tool_name}: {msg}")

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
