import os
from ament_index_python.packages import get_package_share_directory

from launch_ros.actions import Node
from launch import LaunchDescription, LaunchService
from launch.actions import IncludeLaunchDescription, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource

def launch_setup(context):
    lidar_receiver_package_path = get_package_share_directory('lidar_receiver')

    lidar_receiver_node = Node(
        package='lidar_receiver',
        executable='lidar_receiver_node',
        name='lidar_receiver',
        parameters=[{
            'input_topic': '/pi3/scan',
            'output_topic': 'scan_raw'
        }],
        output='screen',
    )

    laser_filters_config = os.path.join(lidar_receiver_package_path, 'config/lidar_filters_config.yaml')
    laser_filter_node = Node(
        package='laser_filters',
        executable='scan_to_scan_filter_chain',
        output='screen',
        parameters=[laser_filters_config, {'hw_id': 'none'}],
        remappings=[('scan', 'scan_raw'),
                    ('scan_filtered', 'scan')]
    )

    return [lidar_receiver_node, laser_filter_node]

def generate_launch_description():
    return LaunchDescription([
        OpaqueFunction(function = launch_setup)
    ])

if __name__ == '__main__':
    ld = generate_launch_description()
    ls = LaunchService()
    ls.include_launch_description(ld)
    ls.run()