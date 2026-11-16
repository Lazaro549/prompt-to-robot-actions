"""
Amazon Bedrock planner using Claude models with tool use.

Requires:
    pip install boto3
    AWS credentials configured (env vars, profile, or IAM role)
"""

from __future__ import annotations

import json
from typing import Any

from src.planner.planner import Plan, PlanStep
from src.tools.definitions import ROBOT_TOOLS

try:
    import boto3
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "boto3 is required for Bedrock planning. Install with: pip install boto3"
    ) from exc


SYSTEM_PROMPT = """You are a robot task planner.

Convert the user instruction into a sequence of robot tool calls.
Use ONLY the provided tools. Prefer the smallest correct plan.
When finished, stop.
"""


def _tools_for_bedrock() -> list[dict[str, Any]]:
    """Convert our ROBOT_TOOLS into Bedrock Converse toolConfig format."""
    tools = []
    for t in ROBOT_TOOLS:
        tools.append(
            {
                "toolSpec": {
                    "name": t["name"],
                    "description": t["description"],
                    "inputSchema": {"json": t["input_schema"]},
                }
            }
        )
    return tools


class BedrockPlanner:
    """
    Planner that calls Claude on Amazon Bedrock via the Converse API.

    Example:
        planner = BedrockPlanner(model_id="anthropic.claude-3-5-sonnet-20241022-v2:0")
        plan = planner.plan("Pick the red cube")
    """

    def __init__(
        self,
        model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0",
        region: str = "us-east-1",
        max_tokens: int = 1024,
    ):
        self.model_id = model_id
        self.max_tokens = max_tokens
        self.client = boto3.client("bedrock-runtime", region_name=region)

    def plan(self, prompt: str) -> Plan:
        response = self.client.converse(
            modelId=self.model_id,
            system=[{"text": SYSTEM_PROMPT}],
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            toolConfig={"tools": _tools_for_bedrock()},
            inferenceConfig={"maxTokens": self.max_tokens},
        )

        steps: list[PlanStep] = []
        raw_parts: list[str] = []

        output_message = response.get("output", {}).get("message", {})
        for block in output_message.get("content", []):
            if "toolUse" in block:
                tu = block["toolUse"]
                steps.append(
                    PlanStep(
                        tool_name=tu["name"],
                        arguments=dict(tu.get("input", {})),
                    )
                )
                raw_parts.append(f"toolUse:{tu['name']}({tu.get('input')})")
            elif "text" in block:
                raw_parts.append(block["text"])

        if not steps:
            steps.append(
                PlanStep(
                    tool_name="wait",
                    arguments={"seconds": 1.0},
                    reasoning="Bedrock returned no tool calls",
                )
            )

        # Token usage (when available)
        usage = response.get("usage", {})
        extra = {
            "input_tokens": usage.get("inputTokens", 0),
            "output_tokens": usage.get("outputTokens", 0),
        }

        plan = Plan(
            original_prompt=prompt,
            steps=steps,
            raw_llm_response=" | ".join(raw_parts),
        )
        # Attach usage for the logger
        plan._bedrock_usage = extra  # type: ignore[attr-defined]
        return plan
