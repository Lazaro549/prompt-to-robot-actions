from src.safety import ForbiddenZone, SafetyGuard


def test_allow_list():
    guard = SafetyGuard(allowed_tools={"pick", "wait"})
    ok, err = guard.check("fly", {})
    assert not ok and err


def test_forbidden_zone():
    guard = SafetyGuard(
        forbidden_zones=[ForbiddenZone(-1.0, -0.5, 0.0, 1.0, name="no_go")]
    )
    ok, err = guard.check("move_to", {"x": -0.7, "y": 0.5, "z": 0.1})
    assert not ok
    assert "no_go" in (err or "")

    ok2, _ = guard.check("move_to", {"x": 0.5, "y": 0.5, "z": 0.1})
    assert ok2
