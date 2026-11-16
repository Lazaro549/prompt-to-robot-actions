"""
Full simulation stack for prompt-to-robot-actions.

Includes:
  1. Gazebo (ros_gz_sim)
  2. Robot spawn (configurable URDF/SDF or TurtleBot4-style placeholder)
  3. ros_gz_bridge (cmd_vel, odom, clock, camera)
  4. Optional Nav2 bringup hooks

Usage:
  ros2 launch prompt_to_robot_gazebo full_stack.launch.py
  ros2 launch prompt_to_robot_gazebo full_stack.launch.py use_nav2:=true

Replace `robot_model` / spawn args with your real URDF or a TurtleBot4
package when available on the machine.
"""

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    GroupAction,
    IncludeLaunchDescription,
    TimerAction,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description() -> LaunchDescription:
    use_nav2 = LaunchConfiguration("use_nav2")
    use_sim_time = LaunchConfiguration("use_sim_time")
    world = LaunchConfiguration("world")
    robot_name = LaunchConfiguration("robot_name")

    args = [
        DeclareLaunchArgument("use_nav2", default_value="false"),
        DeclareLaunchArgument("use_sim_time", default_value="true"),
        DeclareLaunchArgument("world", default_value="empty.sdf"),
        DeclareLaunchArgument("robot_name", default_value="robot"),
    ]

    # --- Gazebo ---
    gz_sim = ExecuteProcess(
        cmd=["ros2", "launch", "ros_gz_sim", "gz_sim.launch.py", ["gz_args:=-r ", world]],
        output="screen",
    )

    # --- Spawn robot ---
    # Prefer a real model when present. This uses ros_gz_sim create with a
    # minimal placeholder; swap entity/file for TurtleBot4 or your URDF.
    spawn_robot = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-name", robot_name,
            "-x", "0.0",
            "-y", "0.0",
            "-z", "0.1",
            # Uncomment and point to your model:
            # "-file", "/path/to/robot.sdf",
            # or: "-topic", "robot_description",
        ],
        output="screen",
    )

    # If you have robot_state_publisher + URDF:
    # robot_state_publisher = Node(
    #     package="robot_state_publisher",
    #     executable="robot_state_publisher",
    #     parameters=[{"use_sim_time": use_sim_time, "robot_description": urdf}],
    # )

    # --- Bridges ---
    clock_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=["/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock"],
        output="screen",
    )

    cmd_vel_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=["/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist"],
        parameters=[{"use_sim_time": use_sim_time}],
        output="screen",
    )

    odom_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            "/model/robot/odometry@nav_msgs/msg/Odometry[gz.msgs.Odometry",
        ],
        remappings=[("/model/robot/odometry", "/odom")],
        parameters=[{"use_sim_time": use_sim_time}],
        output="screen",
    )

    camera_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            "/camera@sensor_msgs/msg/Image[gz.msgs.Image",
        ],
        remappings=[("/camera", "/camera/image_raw")],
        parameters=[{"use_sim_time": use_sim_time}],
        output="screen",
    )

    bridges = TimerAction(
        period=2.0,
        actions=[clock_bridge, cmd_vel_bridge, odom_bridge, camera_bridge],
    )

    # --- Nav2 (optional) ---
    # Expects nav2_bringup installed. Uses the standard tb3/simulation-style
    # bringup when available; otherwise this group is skipped unless use_nav2.
    nav2_group = GroupAction(
        condition=IfCondition(use_nav2),
        actions=[
            # Include Nav2 bringup if the package exists on the system.
            # Users should point params_file to their map/costmap config.
            ExecuteProcess(
                cmd=[
                    "ros2",
                    "launch",
                    "nav2_bringup",
                    "navigation_launch.py",
                    "use_sim_time:=true",
                ],
                output="screen",
            ),
        ],
    )

    return LaunchDescription(
        args
        + [
            gz_sim,
            TimerAction(period=3.0, actions=[spawn_robot]),
            bridges,
            TimerAction(period=6.0, actions=[nav2_group]),
        ]
    )
