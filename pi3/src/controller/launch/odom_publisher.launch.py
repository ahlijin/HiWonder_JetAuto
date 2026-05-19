import os
from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription, LaunchService
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription

def generate_launch_description():
    namespace = LaunchConfiguration('namespace', default='')
    use_namespace = LaunchConfiguration('use_namespace', default='false')
    odom_frame = LaunchConfiguration('odom_frame', default='odom')
    base_frame = LaunchConfiguration('base_frame', default='base_footprint')
    imu_frame = LaunchConfiguration('imu_frame', default='imu_link')
    frame_prefix = LaunchConfiguration('frame_prefix', default='')

    namespace_arg = DeclareLaunchArgument('namespace', default_value=namespace)
    use_namespace_arg = DeclareLaunchArgument('use_namespace', default_value=use_namespace)
    odom_frame_arg = DeclareLaunchArgument('odom_frame', default_value=odom_frame)
    base_frame_arg = DeclareLaunchArgument('base_frame', default_value=base_frame)
    imu_frame_arg = DeclareLaunchArgument('imu_frame', default_value=imu_frame)
    frame_prefix_arg = DeclareLaunchArgument('frame_prefix', default_value=frame_prefix)

    robot_controller_package_path = get_package_share_directory('ros_robot_controller')
    controller_package_path = get_package_share_directory('controller')

    robot_controller_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(robot_controller_package_path, 'launch/ros_robot_controller.launch.py')
        ]),
        launch_arguments={
            'imu_frame': imu_frame,
        }.items()
    )

    odom_publisher_node = Node(
        package='controller',
        executable='odom_publisher',
        name='odom_publisher',
        output='screen',
        parameters=[os.path.join(controller_package_path, 'config/calibrate_params.yaml'), {
            'base_frame_id': base_frame, 
            'odom_frame_id': odom_frame,
            'pub_odom_topic': True,
            }],  
    )

    return LaunchDescription([
        namespace_arg,
        use_namespace_arg,
        odom_frame_arg,
        base_frame_arg,
        imu_frame_arg,
        frame_prefix_arg,
        robot_controller_launch,
        odom_publisher_node
    ])

if __name__ == '__main__':
    # 创建一个LaunchDescription对象(Create a LaunchDescription object)
    ld = generate_launch_description()

    ls = LaunchService()
    ls.include_launch_description(ld)
    ls.run()
