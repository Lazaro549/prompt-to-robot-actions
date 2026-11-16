"""Estimate and persist LLM cost from token usage."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

# Approximate USD per 1M tokens (update as pricing changes)
PRICING_PER_1M = {
    "claude-sonnet-4-5": {"input": 3.0, "output": 15.0},
    "claude-sonnet-4": {"input": 3.0, "output": 15.0},
    "claude-opus-4": {"input": 15.0, "output": 75.0},
    "anthropic.claude-3-5-sonnet-20241022-v2:0": {"input": 3.0, "output": 15.0},
    "default": {"input": 3.0, "output": 15.0},
}


@dataclass
class CostEstimate:
    model: str
    input_tokens: int
    output_tokens: int
    input_cost_usd: float
    output_cost_usd: float
    total_cost_usd: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def estimate_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
) -> CostEstimate:
    rates = PRICING_PER_1M.get(model, PRICING_PER_1M["default"])
    in_cost = (input_tokens / 1_000_000) * rates["input"]
    out_cost = (output_tokens / 1_000_000) * rates["output"]
    return CostEstimate(
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        input_cost_usd=round(in_cost, 6),
        output_cost_usd=round(out_cost, 6),
        total_cost_usd=round(in_cost + out_cost, 6),
    )
