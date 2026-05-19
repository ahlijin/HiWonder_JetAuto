import os
from ament_index_python.packages import get_package_share_directory

from launch_ros.actions import Node
from launch import LaunchDescription, LaunchService
from launch.actions import IncludeLaunchDescription, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource

def launch_setup(context):
    jetauto_peripherals_package_path = get_package_share_directory('jetauto_peripherals')
    slam_package_path = get_package_share_directory('slam')

    depth_camera_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(jetauto_peripherals_package_path, 'launch/depth_camera.launch.py')),
    )

    lidar_receiver_node = Node(
        package='lidar_receiver',
        executable='lidar_receiver_node',
        name='lidar_receiver',
        output='screen',
    )

    slam_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(slam_package_path, 'launch/slam.launch.py')),
    )

    return [
        depth_camera_launch,
        lidar_receiver_node,
        slam_launch,
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
