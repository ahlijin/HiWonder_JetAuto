import os
from launch_ros.actions import Node
from launch import LaunchDescription, LaunchService
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    base_frame = LaunchConfiguration('base_frame', default='base_link')
    base_frame_arg = DeclareLaunchArgument('base_frame', default_value=base_frame)

    # Get package paths using abspath
    servo_controller_package_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    servo_controller_node = Node(
        package='servo_controller',
        executable='servo_controller',
        output='screen',
        parameters=[{'base_frame': base_frame},
                    {'joint1.id': 1},
                    {'joint1.init': 500},
                    {'joint1.min': 1000},
                    {'joint1.max': 0}]
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
