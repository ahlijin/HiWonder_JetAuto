#!/bin/bash
gnome-terminal \
    --tab -e "zsh -c 'source /opt/ros/humble/setup.bash; source ~/jetson_ws/install/setup.bash; export ROS_DOMAIN_ID=42; ros2 launch slam jetson_bringup.launch.py enable_save:=false'" \
    --tab -e "zsh -c 'source /opt/ros/humble/setup.bash; source ~/jetson_ws/install/setup.bash; export ROS_DOMAIN_ID=42; rviz2 -d ~/jetson_ws/src/slam/rviz/slam_desktop.rviz'" \
    --tab -e "zsh -c 'source /opt/ros/humble/setup.bash; source ~/jetson_ws/install/setup.bash; export ROS_DOMAIN_ID=42; ros2 run slam map_save'"
