"""
Nav2 integration stub.

When ROS 2 + Nav2 are running:
  source /opt/ros/$ROS_DISTRO/setup.bash
  python -m examples.nav2_integration_stub

Without ROS, prints the expected flow and exits 0 (documentation mode).
"""

from __future__ import annotations

import sys


def main() -> int:
    try:
        from src.backends.nav2_client import Nav2Client
    except ImportError as exc:
        print("Nav2Client import failed:", exc)
        return 1

    try:
        client = Nav2Client()
    except ImportError:
        print("ROS 2 / rclpy not available.")
        print("Expected flow when stack is up:")
        print("  1. Nav2Client.navigate_to(x, y)")
        print("  2. Wait for NavigateToPose result")
        print("  3. Return success + status to the agent")
        return 0

    result = client.navigate_to(1.5, 0.5)
    print(result)
    client.shutdown()
    return 0 if result.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main())
