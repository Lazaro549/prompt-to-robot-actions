"""LLM-based planner that converts natural language into structured robot plans."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from src.tools.definitions import ROBOT_TOOLS


@dataclass
class PlanStep:
    tool_name: str
    arguments: dict[str, Any]
    reasoning: str | None = None


@dataclass
class Plan:
    original_prompt: str
    steps: list[PlanStep] = field(default_factory=list)
    raw_llm_response: str | None = None
    success: bool | None = None  # filled after evaluation

    def to_dict(self) -> dict[str, Any]:
        return {
            "original_prompt": self.original_prompt,
            "steps": [
                {
                    "tool_name": s.tool_name,
                    "arguments": s.arguments,
                    "reasoning": s.reasoning,
                }
                for s in self.steps
            ],
            "success": self.success,
        }


class Planner:
    """
    Converts a natural language prompt into a sequence of tool calls.

    Currently uses a simple rule-based fallback.
    Later this will call Claude / Bedrock with the ROBOT_TOOLS schemas.
    """

    def __init__(self, model: str = "claude-sonnet", use_llm: bool = False):
        self.model = model
        self.use_llm = use_llm

    def plan(self, prompt: str) -> Plan:
        """Generate a plan from a natural language prompt."""
        if self.use_llm:
            return self._plan_with_llm(prompt)
        return self._plan_fallback(prompt)

    def _plan_with_llm(self, prompt: str) -> Plan:
        """
        Placeholder for real LLM planning.

        In the next iteration this will:
        1. Send the prompt + ROBOT_TOOLS to Claude / Bedrock
        2. Parse the tool-use response into PlanStep objects
        """
        raise NotImplementedError(
            "LLM planning not yet implemented. Set use_llm=False for the fallback planner."
        )

    def _plan_fallback(self, prompt: str) -> Plan:
        """
        Very simple keyword-based planner for early testing.
        Only meant as a scaffold until the real LLM planner is ready.
        """
        prompt_lower = prompt.lower()
        steps: list[PlanStep] = []

        if "pick" in prompt_lower or "grab" in prompt_lower:
            # naive extraction
            object_id = "object_1"
            if "red" in prompt_lower:
                object_id = "red_cube"
            elif "blue" in prompt_lower:
                object_id = "blue_cube"

            steps.append(
                PlanStep(
                    tool_name="pick",
                    arguments={"object_id": object_id, "force": 0.6},
                    reasoning="Detected pick intent in prompt",
                )
            )

        if "place" in prompt_lower or "put" in prompt_lower:
            steps.append(
                PlanStep(
                    tool_name="place",
                    arguments={"x": 0.4, "y": 0.0, "z": 0.1},
                    reasoning="Detected place intent",
                )
            )

        if "move" in prompt_lower or "go to" in prompt_lower:
            steps.append(
                PlanStep(
                    tool_name="move_to",
                    arguments={"x": 0.3, "y": 0.2, "z": 0.25, "frame": "world"},
                    reasoning="Detected move intent",
                )
            )

        if "inspect" in prompt_lower or "look" in prompt_lower:
            steps.append(
                PlanStep(
                    tool_name="inspect",
                    arguments={"target": "current_area", "sensor": "camera"},
                    reasoning="Detected inspect intent",
                )
            )

        if not steps:
            steps.append(
                PlanStep(
                    tool_name="wait",
                    arguments={"seconds": 1.0},
                    reasoning="No clear action detected — defaulting to wait",
                )
            )

        return Plan(original_prompt=prompt, steps=steps)
