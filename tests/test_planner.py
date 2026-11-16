"""Tests for the fallback planner."""

from src.planner.planner import Planner


def test_pick_and_place():
    plan = Planner(use_llm=False).plan("Pick the red cube and place it on the table")
    names = [s.tool_name for s in plan.steps]
    assert "pick" in names
    assert "place" in names
    pick = next(s for s in plan.steps if s.tool_name == "pick")
    assert pick.arguments["object_id"] == "red_cube"


def test_blue_cube():
    plan = Planner(use_llm=False).plan("Grab the blue cube")
    pick = plan.steps[0]
    assert pick.tool_name == "pick"
    assert pick.arguments["object_id"] == "blue_cube"


def test_navigate_keywords():
    plan = Planner(use_llm=False).plan("Move to the shelf")
    assert any(s.tool_name == "move_to" for s in plan.steps)


def test_default_wait():
    plan = Planner(use_llm=False).plan("Hello robot")
    assert plan.steps[0].tool_name == "wait"
