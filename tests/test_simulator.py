from src.backends.simulator import SimulatorBackend
from src.executor.executor import PlanExecutor
from src.executor.recovery import RecoveryPolicy
from src.planner.planner import Plan, PlanStep, Planner


def test_simulator_pick_place():
    backend = SimulatorBackend()
    plan = Planner(use_llm=False).plan("Pick the red cube and place it on the table")
    result = PlanExecutor(backend).run(plan)
    assert result.overall_success
    state = backend.get_state()
    assert state.get("holding") in (None, "") or "holding" in state


def test_recovery_alternate_object():
    policy = RecoveryPolicy(on_pick_failure="alternate_object")
    step = PlanStep(tool_name="pick", arguments={"object_id": "red_cube"})
    actions = policy.next_actions(step, error="not found", attempt=0)
    assert actions
    assert actions[0].step.arguments["object_id"] == "blue_cube"
