"""
Launch Gazebo (Ignition/Harmonic or Fortress via ros_gz) with a simple empty world
and the standard bridges needed by prompt-to-robot-actions.

Usage (after building the workspace):

  source /opt/ros/$ROS_DISTRO/setup.bash
  source ros2_ws/install/setup.bash
  ros2 launch prompt_to_robot_gazebo gazebo_sim.launch.py

Then in another terminal run the Python agent against GazeboROS2Backend.

Notes:
- This launch is intentionally minimal. Replace the world and spawn your own
  robot URDF/SDF for a real demo.
- Bridge topics match GazeboROS2Config defaults in src/backends/gazebo_ros2.py.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, TimerAction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    world = LaunchConfiguration("world")
    use_sim_time = LaunchConfiguration("use_sim_time")

    declare_world = DeclareLaunchArgument(
        "world",
        default_value="empty.sdf",
        description="Gazebo world file (name or absolute path)",
    )
    declare_sim_time = DeclareLaunchArgument(
        "use_sim_time",
        default_value="true",
        description="Use simulation clock",
    )

    # Start Gazebo (ros_gz_sim). Works with Gazebo Harmonic / Fortress.
    gz_sim = ExecuteProcess(
        cmd=["ros2", "launch", "ros_gz_sim", "gz_sim.launch.py", ["gz_args:=-r ", world]],
        output="screen",
    )

    # Bridge: Gazebo clock → ROS /clock
    clock_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=["/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock"],
        output="screen",
    )

    # Bridge: ROS /cmd_vel → Gazebo (adjust topic to your robot model)
    # Example for a differential drive plugin that listens on /model/robot/cmd_vel
    cmd_vel_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            "/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist",
        ],
        output="screen",
        parameters=[{"use_sim_time": use_sim_time}],
    )

    # Optional: pose / odometry bridge (uncomment and adapt to your model name)
    # odom_bridge = Node(
    #     package="ros_gz_bridge",
    #     executable="parameter_bridge",
    #     arguments=[
    #         "/model/robot/odometry@nav_msgs/msg/Odometry[gz.msgs.Odometry",
    #     ],
    #     remappings=[("/model/robot/odometry", "/odom")],
    #     output="screen",
    # )

    return LaunchDescription(
        [
            declare_world,
            declare_sim_time,
            gz_sim,
            TimerAction(period=2.0, actions=[clock_bridge, cmd_vel_bridge]),
        ]
    )
