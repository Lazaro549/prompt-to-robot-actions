"""
Claude-based planner using Anthropic tool use.

This module asks Claude to produce a sequence of tool calls that represent
the robot plan. The tools are NOT executed here — that is the job of the
PlanExecutor + backend.
"""

from __future__ import annotations

import os
from typing import Any

from src.planner.planner import Plan, PlanStep
from src.tools.definitions import ROBOT_TOOLS

try:
    from anthropic import Anthropic
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "anthropic package is required for Claude planning. "
        "Install it with: pip install anthropic"
    ) from exc


SYSTEM_PROMPT = """You are a robot task planner.

Your job is to convert a natural language instruction into a sequence of
robot tool calls. You must ONLY use the provided tools.

Rules:
- Prefer the smallest number of steps that correctly achieves the goal.
- Use realistic coordinates when the user does not specify exact numbers.
- If the user mentions a colored object (red, blue, etc.), use that in the object_id.
- Do not invent tools that are not in the list.
- When you are done planning, stop. Do not add explanatory text after the tool calls.
"""


class ClaudePlanner:
    """
    Planner that uses Claude tool use to generate a structured Plan.

    Example:
        planner = ClaudePlanner(model="claude-sonnet-4-5")
        plan = planner.plan("Pick the red cube and place it on the table")
    """

    def __init__(
        self,
        model: str = "claude-sonnet-4-5",
        max_tokens: int = 1024,
        api_key: str | None = None,
    ):
        self.model = model
        self.max_tokens = max_tokens
        self.client = Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))

    def plan(self, prompt: str) -> Plan:
        """Generate a Plan by asking Claude to call the robot tools."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=SYSTEM_PROMPT,
            tools=ROBOT_TOOLS,
            messages=[{"role": "user", "content": prompt}],
        )

        steps: list[PlanStep] = []
        raw_parts: list[str] = []

        for block in response.content:
            if block.type == "tool_use":
                steps.append(
                    PlanStep(
                        tool_name=block.name,
                        arguments=dict(block.input),
                        reasoning=None,
                    )
                )
                raw_parts.append(f"tool_use:{block.name}({block.input})")
            elif block.type == "text":
                raw_parts.append(block.text)

        if not steps:
            # Fallback: if Claude only returned text, create a wait step
            # so the pipeline does not break.
            steps.append(
                PlanStep(
                    tool_name="wait",
                    arguments={"seconds": 1.0},
                    reasoning="Claude did not return any tool calls",
                )
            )

        return Plan(
            original_prompt=prompt,
            steps=steps,
            raw_llm_response=" | ".join(raw_parts),
        )


def plan_with_claude(prompt: str, model: str = "claude-sonnet-4-5") -> Plan:
    """Convenience function."""
    return ClaudePlanner(model=model).plan(prompt)
