import os
from launch_ros.actions import Node
from launch import LaunchDescription, LaunchService
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    base_frame = LaunchConfiguration('base_frame', default='')
    base_frame_arg = DeclareLaunchArgument('base_frame', default_value=base_frame)

    # Get package paths using abspath
    servo_controller_package_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    servo_controller_node = Node(
        package='servo_controller',
        executable='servo_controller',
        output='screen',
        parameters=[os.path.join(servo_controller_package_path, 'config/servo_controller.yaml'), {'base_frame': base_frame}]
    )

    return LaunchDescription([
        base_frame_arg,
        servo_controller_node
    ])

if __name__ == '__main__':
    # 创建一个LaunchDescription对象(Create a LaunchDescription object)
    ld = generate_launch_description()

    ls = LaunchService()
    ls.include_launch_description(ld)
    ls.run()
