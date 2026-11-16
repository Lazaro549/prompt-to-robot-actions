"""Executes a Plan against a robot backend with validation and recovery."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from src.planner.planner import Plan, PlanStep
from src.tools.validation import ValidationError, validate_tool_call


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

    def __init__(
        self,
        backend: RobotBackend,
        stop_on_failure: bool = True,
        validate: bool = True,
        recovery: Any | None = None,
    ):
        self.backend = backend
        self.stop_on_failure = stop_on_failure
        self.validate = validate
        self.recovery = recovery  # optional RecoveryPolicy

    def run(self, plan: Plan) -> ExecutionResult:
        results: list[StepResult] = []
        overall_success = True
        steps = list(plan.steps)
        idx = 0

        while idx < len(steps):
            step = steps[idx]
            attempt = 0
            step_result = self._run_one(step)
            results.append(step_result)

            if step_result.success:
                idx += 1
                continue

            overall_success = False
            if self.recovery is not None:
                actions = self.recovery.next_actions(
                    step, step_result.error, attempt=attempt
                )
                if actions:
                    # Insert recovery steps after current index
                    for offset, action in enumerate(actions):
                        steps.insert(idx + 1 + offset, action.step)
                    idx += 1
                    continue

            if self.stop_on_failure:
                break
            idx += 1

        plan.success = overall_success
        return ExecutionResult(
            plan=plan, step_results=results, overall_success=overall_success
        )

    def _run_one(self, step: PlanStep) -> StepResult:
        try:
            args = step.arguments
            if self.validate:
                args = validate_tool_call(step.tool_name, step.arguments)
            output = self.backend.execute(step.tool_name, args)
            success = bool(output.get("success", False))
            error = output.get("error")
        except ValidationError as exc:
            success = False
            output = {}
            error = f"validation: {exc}"
        except Exception as exc:  # noqa: BLE001
            success = False
            output = {}
            error = str(exc)

        return StepResult(step=step, success=success, output=output, error=error)
