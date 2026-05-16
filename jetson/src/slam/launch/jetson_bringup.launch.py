import os
from ament_index_python.packages import get_package_share_directory

from launch_ros.actions import Node
from launch import LaunchDescription, LaunchService
from launch.substitutions import LaunchConfiguration
from launch.actions import IncludeLaunchDescription, OpaqueFunction, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource

def launch_setup(context):
    peripherals_package_path = get_package_share_directory('peripherals')
    slam_package_path = get_package_share_directory('slam')
    use_depth_camera = LaunchConfiguration('use_depth_camera', default='true').perform(context)
    depth_camera_name = LaunchConfiguration('depth_camera_name', default='camera').perform(context)

    use_depth_camera_arg = DeclareLaunchArgument('use_depth_camera', default_value=use_depth_camera)
    depth_camera_name_arg = DeclareLaunchArgument('depth_camera_name', default_value=depth_camera_name)

    lidar_receiver_node = Node(
        package='lidar_receiver',
        executable='lidar_receiver_node',
        name='lidar_receiver',
        output='screen',
    )

    slam_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(slam_package_path, 'launch/slam.launch.py')),
        launch_arguments={
            'use_depth_camera': use_depth_camera,
            'depth_camera_name': depth_camera_name,
        }.items(),
    )

    return [
        use_depth_camera_arg,
        depth_camera_name_arg,
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
