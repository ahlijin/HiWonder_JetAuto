import os
from ament_index_python.packages import get_package_share_directory

from launch_ros.actions import Node
from launch import LaunchDescription, LaunchService
from launch.actions import IncludeLaunchDescription, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource

def launch_setup(context):
    controller_package_path = get_package_share_directory('controller')
    peripherals_package_path = get_package_share_directory('peripherals')

    controller_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(controller_package_path, 'launch/controller.launch.py')),
    )

    lidar_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(peripherals_package_path, 'launch/lidar.launch.py')),
    )

    lidar_bridge_node = Node(
        package='lidar_bridge',
        executable='lidar_bridge_node',
        name='lidar_bridge',
        parameters=[{
            'input_topic': 'scan_raw',
            'output_topic': '/pi3/scan'
        }],
        output='screen',
    )

    joystick_control_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(peripherals_package_path, 'launch/joystick_control.launch.py')),
    )

    startup_check_node = Node(
        package='bringup',
        executable='startup_check',
        output='screen',
    )

    return [
        startup_check_node,
        controller_launch,
        lidar_launch,
        lidar_bridge_node,
        joystick_control_launch,
    ]

def generate_launch_description():
    return LaunchDescription([
        OpaqueFunction(function = launch_setup)
    ])

if __name__ == '__main__':
    ld = generate_launch_description()
    ls = LaunchService()
    ls.include_launch_description(ld)
    ls.run()
