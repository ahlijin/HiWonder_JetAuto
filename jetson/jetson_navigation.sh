#!/bin/bash
gnome-terminal \
    --tab -e "zsh -c 'source /opt/ros/humble/setup.bash; source ~/jetson_ws/install/setup.bash; export ROS_DOMAIN_ID=42; ros2 launch navigation navigation.launch.py map:=map_01'" \
    --tab -e "zsh -c 'source /opt/ros/humble/setup.bash; source ~/jetson_ws/install/setup.bash; export ROS_DOMAIN_ID=42; rviz2 -d ~/jetson_ws/src/navigation/rviz/navigation_desktop.rviz'"
