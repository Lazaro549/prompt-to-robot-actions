"""Recovery / retry policies when a plan step fails."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from src.planner.planner import PlanStep


@dataclass
class RecoveryAction:
    """A substitute step to try after a failure."""

    step: PlanStep
    reason: str


@dataclass
class RecoveryPolicy:
    """
    Decides what to do when a step fails.

    Strategies:
      - retry_same: re-run the same step up to max_retries
      - alternate_object: for pick, try a fallback object_id
      - inspect_then_retry: insert an inspect step, then retry
      - skip: mark failed and continue
      - abort: stop the plan
    """

    max_retries: int = 1
    alternate_objects: list[str] = field(default_factory=lambda: ["blue_cube", "object_1"])
    on_pick_failure: str = "alternate_object"  # or inspect_then_retry | retry_same | abort
    on_other_failure: str = "retry_same"  # or skip | abort

    def next_actions(
        self,
        failed_step: PlanStep,
        error: str | None,
        attempt: int,
    ) -> list[RecoveryAction]:
        if attempt >= self.max_retries and self.on_other_failure == "abort":
            return []

        if failed_step.tool_name == "pick":
            return self._pick_recovery(failed_step, attempt)

        if self.on_other_failure == "retry_same" and attempt < self.max_retries:
            return [
                RecoveryAction(
                    step=failed_step,
                    reason=f"retry {attempt + 1}/{self.max_retries}: {error}",
                )
            ]
        return []

    def _pick_recovery(self, step: PlanStep, attempt: int) -> list[RecoveryAction]:
        strategy = self.on_pick_failure
        if strategy == "abort":
            return []

        if strategy == "retry_same" and attempt < self.max_retries:
            return [RecoveryAction(step=step, reason=f"retry pick attempt {attempt + 1}")]

        if strategy == "inspect_then_retry":
            actions = [
                RecoveryAction(
                    step=PlanStep(
                        tool_name="inspect",
                        arguments={"target": "current_area", "sensor": "camera"},
                        reasoning="Recovery: inspect before re-pick",
                    ),
                    reason="inspect before retry",
                )
            ]
            if attempt < self.max_retries:
                actions.append(RecoveryAction(step=step, reason="retry pick after inspect"))
            return actions

        if strategy == "alternate_object":
            tried = step.arguments.get("object_id")
            for alt in self.alternate_objects:
                if alt != tried:
                    return [
                        RecoveryAction(
                            step=PlanStep(
                                tool_name="pick",
                                arguments={**step.arguments, "object_id": alt},
                                reasoning=f"Recovery: try alternate object {alt}",
                            ),
                            reason=f"alternate object {alt}",
                        )
                    ]
        return []
