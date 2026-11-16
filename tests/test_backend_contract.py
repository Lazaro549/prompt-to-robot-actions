from src.backends.gazebo_ros2 import MockGazeboBackend
from src.backends.moveit_bridge import MockMoveItBackend
from src.backends.protocol import Backend
from src.backends.simulator import SimulatorBackend


def _assert_contract(backend: Backend) -> None:
    assert isinstance(backend, Backend)
    out = backend.execute("wait", {"seconds": 0.01})
    assert isinstance(out, dict)
    assert "success" in out


def test_simulator_contract():
    _assert_contract(SimulatorBackend())


def test_mock_gazebo_contract():
    _assert_contract(MockGazeboBackend())


def test_mock_moveit_contract():
    _assert_contract(MockMoveItBackend())
