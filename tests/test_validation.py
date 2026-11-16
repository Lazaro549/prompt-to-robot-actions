import pytest

from src.tools.validation import ValidationError, validate_tool_call


def test_valid_pick():
    args = validate_tool_call("pick", {"object_id": "red_cube"})
    assert args["object_id"] == "red_cube"
    assert "force" in args  # default applied


def test_missing_required():
    with pytest.raises(ValidationError):
        validate_tool_call("pick", {})


def test_unknown_tool():
    with pytest.raises(ValidationError):
        validate_tool_call("fly", {})


def test_wait_seconds():
    args = validate_tool_call("wait", {"seconds": 2})
    assert args["seconds"] == 2.0
