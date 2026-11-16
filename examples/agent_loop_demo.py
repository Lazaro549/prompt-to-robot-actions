"""
Multi-turn agent demo: Claude plans, executes, sees results, and can replan.

Requirements:
    pip install anthropic
    export ANTHROPIC_API_KEY=sk-ant-...

Run:
    python -m examples.agent_loop_demo
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.agent.agent_loop import RobotAgent
from src.backends.simulator import SimulatorBackend
from src.logging.run_logger import RunLogger


def main() -> None:
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Error: set ANTHROPIC_API_KEY")
        sys.exit(1)

    prompt = "Pick the red cube. If that fails, try the blue cube. Then place it on the table."

    print("=" * 60)
    print("AGENT PROMPT:", prompt)
    print("=" * 60)

    backend = SimulatorBackend()
    agent = RobotAgent(backend=backend, model="claude-sonnet-4-5", max_turns=6)

    logger = RunLogger(prompt=prompt, planner="claude-agent", model="claude-sonnet-4-5")

    result = agent.run(prompt)

    print("\nEXECUTED STEPS:")
    for i, step in enumerate(result.executed_steps, 1):
        ok = step["result"].get("success")
        status = "✓" if ok else "✗"
        print(f"  {status} {step['tool_name']}({step['arguments']})")
        print(f"     → {step['result'].get('message') or step['result'].get('error')}")

    print("\nSUMMARY:")
    print(f"  Success: {result.final_success}")
    print(f"  Turns: {len(result.turns)}")
    print(f"  Tokens in/out: {result.total_input_tokens} / {result.total_output_tokens}")
    print(f"  Total latency: {result.total_latency_ms} ms")
    print(f"  Stop reason: {result.stop_reason}")

    logger.mark_plan({"steps": result.executed_steps}, latency_ms=result.total_latency_ms)
    logger.mark_execution(
        {"steps": result.executed_steps, "overall_success": result.final_success},
        latency_ms=0,
    )
    logger.add_extra(
        input_tokens=result.total_input_tokens,
        output_tokens=result.total_output_tokens,
        stop_reason=result.stop_reason,
    )
    path = logger.save()
    print(f"\nLog saved to: {path}")

    print("\nFINAL STATE:")
    print(json.dumps(backend.get_state(), indent=2))


if __name__ == "__main__":
    main()
