import os
from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription, LaunchService
from launch.substitutions import LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction

def launch_setup(context):
    enable_save = LaunchConfiguration('enable_save', default='true').perform(context)
    slam_method = LaunchConfiguration('slam_method', default='slam_toolbox').perform(context)
    sim = LaunchConfiguration('sim', default='false').perform(context)
    robot_name = LaunchConfiguration('robot_name', default=os.environ.get('HOST', 'jetson')).perform(context)

    enable_save_arg = DeclareLaunchArgument('enable_save', default_value=enable_save)
    slam_method_arg = DeclareLaunchArgument('slam_method', default_value=slam_method)
    sim_arg = DeclareLaunchArgument('sim', default_value=sim)
    robot_name_arg = DeclareLaunchArgument('robot_name', default_value=robot_name)

    frame_prefix = '' if robot_name == '/' else '%s/'%robot_name
    use_sim_time = 'true' if sim == 'true' else 'false'
    map_frame = '{}map'.format(frame_prefix)
    odom_frame = '{}odom'.format(frame_prefix)
    base_frame = '{}base_footprint'.format(frame_prefix)

    slam_package_path = get_package_share_directory('slam')

    slam_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(slam_package_path, 'launch/include/slam_base.launch.py')),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'map_frame': map_frame,
            'odom_frame': odom_frame,
            'base_frame': base_frame,
            'scan_topic': '/scan',
            'enable_save': enable_save
        }.items(),
    )

    if slam_method == 'slam_toolbox':
        bringup_launch = slam_launch

    return [sim_arg, robot_name_arg, slam_method_arg, bringup_launch]

def generate_launch_description():
    return LaunchDescription([
        OpaqueFunction(function = launch_setup)
    ])

if __name__ == '__main__':
    # 创建一个LaunchDescription对象(Create a LaunchDescription object)
    ld = generate_launch_description()

    ls = LaunchService()
    ls.include_launch_description(ld)
    ls.run()
