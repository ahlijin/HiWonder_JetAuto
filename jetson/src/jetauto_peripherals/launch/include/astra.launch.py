from launch import LaunchDescription, LaunchService
from launch.actions import DeclareLaunchArgument, GroupAction, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node, PushRosNamespace


# Keep `tf_prefix` as a local compatibility argument for the project.
# The rest of the arguments follow `orbbec_ws/astra_camera/launch/astra_pro.launch.xml`.
ARGUMENT_DEFAULTS = [
    ('tf_prefix', ''),
    ('camera_name', 'camera'),
    ('depth_registration', 'false'),
    ('serial_number', ''),
    ('device_num', '1'),
    ('vendor_id', '0'),
    ('product_id', '0'),
    ('enable_point_cloud', 'true'),
    ('enable_colored_point_cloud', 'false'),
    ('point_cloud_qos', 'default'),
    ('connection_delay', '100'),
    ('color_width', '640'),
    ('color_height', '480'),
    ('color_fps', '30'),
    ('enable_color', 'true'),
    ('flip_color', 'false'),
    ('color_qos', 'default'),
    ('color_camera_info_qos', 'default'),
    ('depth_width', '640'),
    ('depth_height', '480'),
    ('depth_fps', '30'),
    ('enable_depth', 'true'),
    ('flip_depth', 'false'),
    ('depth_qos', 'default'),
    ('depth_camera_info_qos', 'default'),
    ('ir_width', '640'),
    ('ir_height', '480'),
    ('ir_fps', '30'),
    ('enable_ir', 'true'),
    ('flip_ir', 'false'),
    ('ir_qos', 'default'),
    ('ir_camera_info_qos', 'default'),
    ('publish_tf', 'true'),
    ('tf_publish_rate', '10.0'),
    ('ir_info_url', ''),
    ('color_info_url', ''),
    ('color_roi_x', '-1'),
    ('color_roi_y', '-1'),
    ('color_roi_width', '-1'),
    ('color_roi_height', '-1'),
    ('depth_roi_x', '-1'),
    ('depth_roi_y', '-1'),
    ('depth_roi_width', '-1'),
    ('depth_roi_height', '-1'),
    ('depth_scale', '1'),
    ('color_depth_synchronization', 'false'),
    ('use_uvc_camera', 'true'),
    ('uvc_vendor_id', '0x2bc5'),
    ('uvc_product_id', '0x0501'),
    ('uvc_retry_count', '100'),
    ('uvc_camera_format', 'mjpeg'),
    ('uvc_flip', 'false'),
    ('oni_log_level', 'verbose'),
    ('oni_log_to_console', 'false'),
    ('oni_log_to_file', 'false'),
    ('enable_d2c_viewer', 'false'),
    ('enable_publish_extrinsic', 'false'),
]

ASTRA_PRO_PARAMETER_NAMES = [name for name, _ in ARGUMENT_DEFAULTS if name != 'tf_prefix']


def launch_setup(context):
    launch_args = [
        DeclareLaunchArgument(name, default_value=default)
        for name, default in ARGUMENT_DEFAULTS
    ]

    tf_prefix = LaunchConfiguration('tf_prefix').perform(context)
    camera_name = LaunchConfiguration('camera_name').perform(context)

    # Match astra_pro.launch.xml: one node under the camera namespace,
    # with parameters passed directly by the launch arguments.
    parameters = [{name: LaunchConfiguration(name) for name in ASTRA_PRO_PARAMETER_NAMES}]

    camera_node = Node(
        package='astra_camera',
        executable='astra_camera_node',
        name='camera',
        output='screen',
        parameters=parameters,
        remappings=[
            ('/tf', '/' + tf_prefix + 'tf'),
            ('/tf_static', '/' + tf_prefix + 'tf_static'),
            ('/' + camera_name + '/depth/color/points', '/' + camera_name + '/depth_registered/points'),
        ],
    )

    action_node = GroupAction(
        actions=[
            PushRosNamespace(camera_name),
            camera_node,
        ]
    )
    return launch_args + [action_node]


def generate_launch_description():
    return LaunchDescription([
        OpaqueFunction(function=launch_setup)
    ])


if __name__ == '__main__':
    ld = generate_launch_description()

    ls = LaunchService()
    ls.include_launch_description(ld)
    ls.run()

