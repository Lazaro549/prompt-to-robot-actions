"""Evaluates the outcome of a plan execution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.executor.executor import ExecutionResult


@dataclass
class EvaluationReport:
    overall_success: bool
    total_steps: int
    successful_steps: int
    failed_steps: int
    failure_reasons: list[str]
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "overall_success": self.overall_success,
            "total_steps": self.total_steps,
            "successful_steps": self.successful_steps,
            "failed_steps": self.failed_steps,
            "failure_reasons": self.failure_reasons,
            "summary": self.summary,
        }


class Evaluator:
    """Produces a simple evaluation report from an ExecutionResult."""

    def evaluate(self, result: ExecutionResult) -> EvaluationReport:
        total = len(result.step_results)
        successful = sum(1 for r in result.step_results if r.success)
        failed = total - successful
        reasons = [r.error for r in result.step_results if r.error]

        if result.overall_success:
            summary = f"Plan succeeded ({successful}/{total} steps)."
        else:
            summary = (
                f"Plan failed ({successful}/{total} steps succeeded). "
                f"Reasons: {'; '.join(reasons) if reasons else 'unknown'}"
            )

        return EvaluationReport(
            overall_success=result.overall_success,
            total_steps=total,
            successful_steps=successful,
            failed_steps=failed,
            failure_reasons=reasons,
            summary=summary,
        )
