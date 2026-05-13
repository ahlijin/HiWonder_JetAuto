import os
from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription, LaunchService
from launch.substitutions import LaunchConfiguration
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, GroupAction
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    machine_type = os.environ['MACHINE_TYPE']

    depth_camera_name_arg = DeclareLaunchArgument(
        'depth_camera_name',
        default_value='depth_cam'
    )

    tf_prefix_arg = DeclareLaunchArgument(
        'tf_prefix',
        default_value=''
    )

    app_arg = DeclareLaunchArgument(
        'app',
        default_value='false'
    )

    peripherals_package_path = get_package_share_directory('peripherals')
    
    if machine_type == 'JetAutoPro':
        camera_launch = GroupAction([
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(os.path.join(peripherals_package_path, 'launch/include/astra.launch.py')),
        launch_arguments={
            'camera_name': LaunchConfiguration('depth_camera_name'),
            'tf_prefix': LaunchConfiguration('tf_prefix'),
        }.items()
            ),
        ])
    else:
        camera_launch = GroupAction([
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(os.path.join(peripherals_package_path, 'launch/include/astra.launch.py')),
        launch_arguments={
            'camera_name': LaunchConfiguration('depth_camera_name'),
            'tf_prefix': LaunchConfiguration('tf_prefix'),
        }.items()
            ),
        ])

    # dabai_dcw_launch = IncludeLaunchDescription(
        # PythonLaunchDescriptionSource(os.path.join(peripherals_package_path, 'launch/include/astra.launch.py')),
        # launch_arguments={
            # 'camera_name': LaunchConfiguration('depth_camera_name'),
            # 'tf_prefix': LaunchConfiguration('tf_prefix'),
        # }.items()
    # )

    return LaunchDescription([
        depth_camera_name_arg,
        tf_prefix_arg,
        app_arg,
        # dabai_dcw_launch
        camera_launch
    ])

if __name__ == '__main__':
    # 创建一个LaunchDescription对象(Create a LaunchDescription object)
    ld = generate_launch_description()

    ls = LaunchService()
    ls.include_launch_description(ld)
    ls.run()

