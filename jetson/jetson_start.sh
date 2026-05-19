#!/bin/bash

source /opt/ros/humble/setup.bash
source ~/jetson_ws/install/setup.bash

export ROS_DOMAIN_ID=42

ros2 launch slam jetson_bringup.launch.py use_depth_camera:=true depth_camera_name:=camera