#!/bin/bash

set -e

gnome-terminal \
    --tab -- bash -lc "source /opt/ros/humble/setup.bash; source ~/jetson_ws/install/setup.bash; export ROS_DOMAIN_ID=42; ros2 launch slam jetson_bringup.launch.py enable_save:=false use_depth_camera:=true depth_camera_name:=camera" \
    --tab -- bash -lc "source /opt/ros/humble/setup.bash; source ~/jetson_ws/install/setup.bash; export ROS_DOMAIN_ID=42; rviz2 -d ~/jetson_ws/src/slam/rviz/slam_desktop.rviz" \
    --tab -- bash -lc "source /opt/ros/humble/setup.bash; source ~/jetson_ws/install/setup.bash; export ROS_DOMAIN_ID=42; ros2 run slam map_save"
