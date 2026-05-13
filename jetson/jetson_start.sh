#!/bin/bash

source /opt/ros/humble/setup.bash
source ~/jetson_ws/jetson_env.sh
source ~/jetson_ws/install/setup.bash

ros2 launch slam jetson_bringup.launch.py