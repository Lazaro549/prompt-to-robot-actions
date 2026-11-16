import json
from pathlib import Path

from src.planner.planner import Planner

GOLDEN = Path(__file__).resolve().parents[1] / "data" / "golden_prompts.json"


def test_golden_prompts_fallback():
    cases = json.loads(GOLDEN.read_text())
    planner = Planner(use_llm=False)
    for case in cases:
        plan = planner.plan(case["prompt"])
        names = {s.tool_name for s in plan.steps}
        expected = set(case["expected_tools"])
        assert names & expected, f"{case['id']}: got {names}, expected some of {expected}"
        if "expected_pick_object" in case:
            picks = [s for s in plan.steps if s.tool_name == "pick"]
            assert picks, case["id"]
            assert picks[0].arguments.get("object_id") == case["expected_pick_object"]
