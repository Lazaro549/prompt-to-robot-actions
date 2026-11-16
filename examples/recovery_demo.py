"""
Demo: pick fails for red_cube → recovery tries blue_cube.

Uses a backend that rejects red_cube once, then succeeds on alternate.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.executor.executor import PlanExecutor
from src.executor.recovery import RecoveryPolicy
from src.planner.planner import Plan, PlanStep


class FlakyPickBackend:
    def __init__(self):
        self.calls: list[str] = []

    def execute(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if tool_name != "pick":
            return {"success": True, "message": f"ok {tool_name}"}
        oid = arguments.get("object_id", "")
        self.calls.append(oid)
        if oid == "red_cube":
            return {"success": False, "error": "red_cube not reachable"}
        return {"success": True, "message": f"Picked {oid}", "holding": oid}


def main() -> None:
    plan = Plan(
        original_prompt="Pick the red cube",
        steps=[PlanStep(tool_name="pick", arguments={"object_id": "red_cube", "force": 0.5})],
    )
    backend = FlakyPickBackend()
    policy = RecoveryPolicy(on_pick_failure="alternate_object", max_retries=1)
    result = PlanExecutor(backend, stop_on_failure=True, recovery=policy).run(plan)

    print("Calls:", backend.calls)
    print("Steps executed:")
    for r in result.step_results:
        status = "OK" if r.success else "FAIL"
        print(f"  [{status}] {r.step.tool_name} {r.step.arguments} -> {r.output or r.error}")
    print("Overall success:", result.overall_success)


if __name__ == "__main__":
    main()
