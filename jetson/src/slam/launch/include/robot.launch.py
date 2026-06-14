import os
from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription, LaunchService
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, OpaqueFunction

def launch_setup(context):
    sim = LaunchConfiguration('sim', default='false').perform(context)
    use_joy = LaunchConfiguration('use_joy', default='true').perform(context)
    use_depth_camera = LaunchConfiguration('use_depth_camera', default='false').perform(context)
    master_name = LaunchConfiguration('master_name', default='/').perform(context)
    robot_name = LaunchConfiguration('robot_name', default='/').perform(context)
    depth_camera_name = LaunchConfiguration('depth_camera_name', default='camera').perform(context)
    action_name = LaunchConfiguration('action_name', default='init').perform(context)

    sim_arg = DeclareLaunchArgument('sim', default_value=sim)
    master_name_arg = DeclareLaunchArgument('master_name', default_value=master_name)
    robot_name_arg = DeclareLaunchArgument('robot_name', default_value=robot_name)
    depth_camera_name_arg = DeclareLaunchArgument('depth_camera_name', default_value=depth_camera_name)
    use_joy_arg = DeclareLaunchArgument('use_joy', default_value=use_joy)
    use_depth_camera_arg = DeclareLaunchArgument('use_depth_camera', default_value=use_depth_camera)
    action_name_arg = DeclareLaunchArgument('action_name', default_value=action_name)

    jetauto_peripherals_package_path = get_package_share_directory('jetauto_peripherals')

    depth_camera_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(jetauto_peripherals_package_path, 'launch/depth_camera.launch.py')),
        condition=IfCondition(use_depth_camera),
        launch_arguments={
            'depth_camera_name': depth_camera_name,
            'tf_prefix': '' if robot_name == '/' else '%s/'%robot_name,
        }.items(),
    )

    return [
        sim_arg, master_name_arg, robot_name_arg, depth_camera_name_arg,
        use_joy_arg, use_depth_camera_arg, action_name_arg,
        depth_camera_launch
    ]

def generate_launch_description():
    return LaunchDescription([
        OpaqueFunction(function = launch_setup)
    ])

if __name__ == '__main__':
    ld = generate_launch_description()
