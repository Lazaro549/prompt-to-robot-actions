"""Structured JSON logging for plans, executions, tokens and latency."""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0

    def add(self, input_tokens: int, output_tokens: int) -> None:
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.total_tokens = self.input_tokens + self.output_tokens


@dataclass
class RunLog:
    run_id: str
    started_at: str
    prompt: str
    planner: str  # "fallback" | "claude" | "bedrock"
    model: str | None = None
    plan_steps: list[dict[str, Any]] = field(default_factory=list)
    execution_steps: list[dict[str, Any]] = field(default_factory=list)
    evaluation: dict[str, Any] = field(default_factory=dict)
    token_usage: dict[str, int] = field(default_factory=dict)
    latency_ms: dict[str, float] = field(default_factory=dict)
    overall_success: bool | None = None
    finished_at: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class RunLogger:
    """
    Collects structured data for a single pipeline run and can write it to disk.

    Usage:
        logger = RunLogger(prompt="Pick the red cube", planner="claude", model="claude-sonnet-4-5")
        logger.mark_plan(plan_dict, latency_ms=320.5, tokens=(1200, 85))
        logger.mark_execution(execution_dict, latency_ms=12.0)
        logger.mark_evaluation(report_dict)
        path = logger.save()
    """

    def __init__(
        self,
        prompt: str,
        planner: str,
        model: str | None = None,
        log_dir: str | Path = "logs",
    ):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self._start = time.perf_counter()
        self.run = RunLog(
            run_id=str(uuid.uuid4())[:8],
            started_at=datetime.now(timezone.utc).isoformat(),
            prompt=prompt,
            planner=planner,
            model=model,
        )
        self._tokens = TokenUsage()

    def mark_plan(
        self,
        plan_dict: dict[str, Any],
        latency_ms: float,
        tokens: tuple[int, int] | None = None,
    ) -> None:
        self.run.plan_steps = plan_dict.get("steps", [])
        self.run.latency_ms["planning"] = round(latency_ms, 2)
        if tokens:
            self._tokens.add(tokens[0], tokens[1])

    def mark_execution(
        self,
        execution_dict: dict[str, Any],
        latency_ms: float,
    ) -> None:
        self.run.execution_steps = execution_dict.get("steps", [])
        self.run.overall_success = execution_dict.get("overall_success")
        self.run.latency_ms["execution"] = round(latency_ms, 2)

    def mark_evaluation(self, report_dict: dict[str, Any]) -> None:
        self.run.evaluation = report_dict
        if "overall_success" in report_dict:
            self.run.overall_success = report_dict["overall_success"]

    def add_extra(self, **kwargs: Any) -> None:
        self.run.extra.update(kwargs)

    def finish(self) -> RunLog:
        total_ms = (time.perf_counter() - self._start) * 1000
        self.run.latency_ms["total"] = round(total_ms, 2)
        self.run.token_usage = {
            "input_tokens": self._tokens.input_tokens,
            "output_tokens": self._tokens.output_tokens,
            "total_tokens": self._tokens.total_tokens,
        }
        self.run.finished_at = datetime.now(timezone.utc).isoformat()
        return self.run

    def save(self, filename: str | None = None) -> Path:
        self.finish()
        name = filename or f"run_{self.run.run_id}_{int(time.time())}.json"
        path = self.log_dir / name
        path.write_text(json.dumps(self.run.to_dict(), indent=2, ensure_ascii=False))
        return path
