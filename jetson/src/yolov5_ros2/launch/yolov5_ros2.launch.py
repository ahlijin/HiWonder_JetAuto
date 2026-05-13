# yolo_v5_ros2_launch.py

import os
import launch
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration  


def launch_setup(context):
    start = LaunchConfiguration('start', default='false')
    start_arg = DeclareLaunchArgument('start', default_value=start)
    package_share_directory = get_package_share_directory('yolov5_ros2')
    peripherals_package_path = get_package_share_directory('peripherals')
    machine_type = os.environ['MACHINE_TYPE']
    if machine_type == 'JetAuto':
        image_topic ="/depth_cam/rgb/image_raw"
    
    elif machine_type == 'JetAutoPro':
        image_topic ="/usb_cam/image_raw"

    model_name = LaunchConfiguration('model', default='yolov5s').perform(context)  
    
    depth_camera_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(peripherals_package_path, 'launch/depth_camera.launch.py')),
    )
    yolov5_ros2_node = Node(
        package='yolov5_ros2',
        executable='yolo_detect',
        output='screen',
        parameters=[
            {"device": "cpu",
            "model": model_name,
            "image_topic":image_topic, 
            "camera_info_topic": "/camera/camera_info",
            "camera_info_file": f"{package_share_directory}/config/camera_info.yaml",
            # "show_result": True,
            "pub_result_img": True,
            'start': start}

        ]
    )

    return [start_arg,
            yolov5_ros2_node,
            # depth_camera_launch,
            ]
    
    
def generate_launch_description():  
    return LaunchDescription([  
        DeclareLaunchArgument(  
            'model',  
            default_value='yolov5s',  
            description='Model to use for YOLOv5 detection'  
        ),  
        OpaqueFunction(function=launch_setup),  
    ])

if __name__ == '__main__':

    ld = generate_launch_description()

    ls = LaunchService()
    ls.include_launch_description(ld)
    ls.run()


