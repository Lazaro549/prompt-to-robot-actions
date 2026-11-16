"""
Multi-turn agent loop.

Claude plans → we execute one (or more) tools → we send the results back
→ Claude can replan or finish.

This is the classic tool-use agent pattern, adapted to our robot pipeline.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Protocol

from src.planner.planner import Plan, PlanStep
from src.tools.definitions import ROBOT_TOOLS

try:
    from anthropic import Anthropic
except ImportError as exc:  # pragma: no cover
    raise ImportError("pip install anthropic") from exc


class RobotBackend(Protocol):
    def execute(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]: ...


@dataclass
class AgentTurn:
    role: str  # "assistant" | "tool_result"
    content: Any
    latency_ms: float = 0.0


@dataclass
class AgentResult:
    prompt: str
    final_success: bool
    turns: list[AgentTurn] = field(default_factory=list)
    executed_steps: list[dict[str, Any]] = field(default_factory=list)
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_latency_ms: float = 0.0
    stop_reason: str = ""


SYSTEM_PROMPT = """You are a robot control agent.

You have access to robot tools. Use them to achieve the user's goal.
After each tool result you will see the outcome. You may call more tools
or stop when the goal is complete.

Rules:
- Prefer the minimum number of tool calls.
- If a tool fails, try an alternative or report failure.
- When the goal is achieved, respond with a short confirmation text and stop.
"""


class RobotAgent:
    """
    Multi-turn agent that lets Claude replan based on tool results.

    Example:
        agent = RobotAgent(backend=SimulatorBackend())
        result = agent.run("Pick the red cube and place it on the table")
    """

    def __init__(
        self,
        backend: RobotBackend,
        model: str = "claude-sonnet-4-5",
        max_turns: int = 8,
        max_tokens: int = 1024,
        api_key: str | None = None,
    ):
        self.backend = backend
        self.model = model
        self.max_turns = max_turns
        self.max_tokens = max_tokens
        self.client = Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))

    def run(self, prompt: str) -> AgentResult:
        messages: list[dict[str, Any]] = [{"role": "user", "content": prompt}]
        result = AgentResult(prompt=prompt, final_success=False)
        start = time.perf_counter()

        for _ in range(self.max_turns):
            t0 = time.perf_counter()
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=SYSTEM_PROMPT,
                tools=ROBOT_TOOLS,
                messages=messages,
            )
            latency = (time.perf_counter() - t0) * 1000

            usage = getattr(response, "usage", None)
            if usage:
                result.total_input_tokens += getattr(usage, "input_tokens", 0) or 0
                result.total_output_tokens += getattr(usage, "output_tokens", 0) or 0

            result.turns.append(
                AgentTurn(role="assistant", content=response.content, latency_ms=latency)
            )
            result.stop_reason = response.stop_reason or ""

            # Append assistant message
            messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason != "tool_use":
                # Model decided to stop (end_turn, etc.)
                result.final_success = True
                break

            # Execute every tool_use block
            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue

                exec_result = self.backend.execute(block.name, dict(block.input))
                result.executed_steps.append(
                    {
                        "tool_name": block.name,
                        "arguments": dict(block.input),
                        "result": exec_result,
                    }
                )

                content = json.dumps(exec_result)
                is_error = not exec_result.get("success", False)
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": content,
                        "is_error": is_error,
                    }
                )

            if not tool_results:
                break

            messages.append({"role": "user", "content": tool_results})
            result.turns.append(AgentTurn(role="tool_result", content=tool_results))

        result.total_latency_ms = round((time.perf_counter() - start) * 1000, 2)
        return result
