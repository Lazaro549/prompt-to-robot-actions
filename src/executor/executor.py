"""Executes a Plan against a robot backend."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from src.planner.planner import Plan, PlanStep


class RobotBackend(Protocol):
    def execute(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]: ...


@dataclass
class StepResult:
    step: PlanStep
    success: bool
    output: dict[str, Any]
    error: str | None = None


@dataclass
class ExecutionResult:
    plan: Plan
    step_results: list[StepResult] = field(default_factory=list)
    overall_success: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "original_prompt": self.plan.original_prompt,
            "overall_success": self.overall_success,
            "steps": [
                {
                    "tool_name": r.step.tool_name,
                    "arguments": r.step.arguments,
                    "success": r.success,
                    "output": r.output,
                    "error": r.error,
                }
                for r in self.step_results
            ],
        }


class PlanExecutor:
    """Runs each step of a Plan against a backend."""

    def __init__(self, backend: RobotBackend, stop_on_failure: bool = True):
        self.backend = backend
        self.stop_on_failure = stop_on_failure

    def run(self, plan: Plan) -> ExecutionResult:
        results: list[StepResult] = []
        overall_success = True

        for step in plan.steps:
            try:
                output = self.backend.execute(step.tool_name, step.arguments)
                success = bool(output.get("success", False))
                error = output.get("error")
            except Exception as exc:  # noqa: BLE001
                success = False
                output = {}
                error = str(exc)

            results.append(
                StepResult(step=step, success=success, output=output, error=error)
            )

            if not success:
                overall_success = False
                if self.stop_on_failure:
                    break

        plan.success = overall_success
        return ExecutionResult(plan=plan, step_results=results, overall_success=overall_success)
