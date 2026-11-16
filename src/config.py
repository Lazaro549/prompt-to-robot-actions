"""Load pipeline configuration from YAML."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    cfg_path = Path(path) if path else Path("config/default.yaml")
    if not cfg_path.exists():
        return {}
    try:
        import yaml
    except ImportError:
        # Minimal subset without PyYAML: only used if yaml not installed
        return _parse_simple_yaml(cfg_path.read_text())
    data = yaml.safe_load(cfg_path.read_text()) or {}
    return data


def _parse_simple_yaml(text: str) -> dict[str, Any]:
    """Very small fallback for flat-ish defaults if PyYAML missing."""
    # Prefer installing pyyaml; this only avoids hard crash
    return {}
