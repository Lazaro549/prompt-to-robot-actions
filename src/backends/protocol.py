"""Formal backend contract used across the pipeline."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Backend(Protocol):
    """Any robot backend must implement execute()."""

    def execute(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """
        Run one tool.

        Must return a dict with at least:
          - success: bool
          - message or error: str
        """
        ...


@runtime_checkable
class StatefulBackend(Backend, Protocol):
    def get_state(self) -> dict[str, Any]:
        ...
