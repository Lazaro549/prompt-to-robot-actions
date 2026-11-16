"""LLM-based planner that converts natural language into structured robot plans."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


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
    success: bool | None = None

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


Provider = Literal["claude", "bedrock"]


class Planner:
    def __init__(
        self,
        model: str = "claude-sonnet-4-5",
        use_llm: bool = False,
        provider: Provider = "claude",
    ):
        self.model = model
        self.use_llm = use_llm
        self.provider = provider

    def plan(self, prompt: str) -> Plan:
        if self.use_llm:
            return self._plan_with_llm(prompt)
        return self._plan_fallback(prompt)

    def _plan_with_llm(self, prompt: str) -> Plan:
        if self.provider == "bedrock":
            from src.planner.bedrock_planner import BedrockPlanner

            return BedrockPlanner(model_id=self.model).plan(prompt)

        from src.planner.claude_planner import ClaudePlanner

        return ClaudePlanner(model=self.model).plan(prompt)

    def _plan_fallback(self, prompt: str) -> Plan:
        prompt_lower = prompt.lower()
        steps: list[PlanStep] = []

        if "pick" in prompt_lower or "grab" in prompt_lower:
            object_id = "object_1"
            if "red" in prompt_lower:
                object_id = "red_cube"
            elif "blue" in prompt_lower:
                object_id = "blue_cube"
            steps.append(
                PlanStep(
                    tool_name="pick",
                    arguments={"object_id": object_id, "force": 0.6},
                    reasoning="Detected pick intent",
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

        if "navigate" in prompt_lower:
            location = None
            for name in ("kitchen", "table", "home", "charging_station"):
                if name in prompt_lower:
                    location = name
                    break
            args: dict[str, Any] = {"location": location} if location else {"x": 1.0, "y": 0.0}
            steps.append(
                PlanStep(
                    tool_name="navigate",
                    arguments=args,
                    reasoning="Detected navigate intent",
                )
            )
        elif "move" in prompt_lower or "go to" in prompt_lower:
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

        if "wait" in prompt_lower and not steps:
            steps.append(
                PlanStep(
                    tool_name="wait",
                    arguments={"seconds": 3.0},
                    reasoning="Detected wait intent",
                )
            )

        if not steps:
            steps.append(
                PlanStep(
                    tool_name="wait",
                    arguments={"seconds": 1.0},
                    reasoning="No clear action detected",
                )
            )

        return Plan(original_prompt=prompt, steps=steps)
