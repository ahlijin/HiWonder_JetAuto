# HiWonder JetAuto — Pi3 + Jetson 双机协同 ROS2 项目

## 项目简介
基于 HiWonder JetAuto 思路整理的 Pi3 + Jetson 双机协同 ROS2 项目。
Pi3 负责底层控制与硬件接口，Jetson 负责感知、SLAM、导航等上层算法。

## 硬件分工
| 设备 | 职责 |
|------|------|
| **Pi3** (底层控制层) | 底盘控制 (Mecanum)、舵机、IMU/按键/电池采集、LiDAR 接入、模型描述/TF、cmd_vel 接收 |
| **Jetson** (上层计算层) | LiDAR 滤波、深度相机、SLAM 建图定位、导航规划、RViz、键盘遥控、舵机转向、视觉/语音扩展 |

## 项目结构
```
HiWonder_JetAuto/
├── pi3/                              # Pi3 工作空间
│   ├── pi3_start.sh                  # 启动脚本
│   └── src/
│       ├── bringup/                  # 整体启动
│       ├── controller/               # 底盘控制 (Mecanum 运动学 + 里程计)
│       ├── ros_robot_controller/     # 控制板通信 (电机/舵机/IMU/按键)
│       ├── sllidar_ros2/            # 激光雷达驱动
│       ├── jetauto_description/      # URDF 模型 + STL
│       ├── servo_controller/         # 舵机控制
│       ├── calibration/             # 标定相关
│       ├── imu_calib/               # IMU 标定 (C++, Eigen)
│       ├── peripherals/             # 手柄/键盘/IMU TF
│       └── interfaces/              # 消息与服务定义
├── jetson/                           # Jetson 工作空间
│   ├── jetson_start.sh               # 无界面 SLAM 启动 (ssh)
│   ├── jetson_slam.sh                # 桌面 SLAM 启动 (含 RViz)
│   ├── jetson_navigation.sh          # 导航启动
│   ├── jetson_rviz.sh                # 独立 RViz
│   ├── jetson_teleop.sh              # 键盘控制
│   └── src/
│       ├── jetauto_peripherals/      # 深度相机、键盘遥控、舵机
│       ├── slam/                     # SLAM Toolbox 配置 + 地图
│       ├── navigation/               # Nav2 导航 + RTAB-Map
│       ├── interfaces/               # 自定义消息 (ColorDetect, ObjectInfo 等)
│       ├── orbbec_ws/                # Orbbec 深度相机驱动 (submodule)
│       └── ros_robot_controller_msgs/# 复用的控制板消息
└── Changelog/                        # 版本日志 (0.9.0 ~ 0.9.6)
```

## 编码规范
- **语言**: Python 3.10 (大多数节点), C++ (imu_calib, astra_camera 驱动)
- **ROS2**: Humble, ROS_DOMAIN_ID=42
- **Python 风格**: PEP 8, 4空格缩进
- **Shell 脚本**: 头部含注释说明, set -e 错误处理
- **YAML 配置**: 2空格缩进

## 构建与运行
```bash
# 编译前必须 source ROS2 环境
source /opt/ros/humble/setup.bash

cd /workspace/HiWonder_JetAuto/pi3
colcon \
  --log-base /root/build/HiWonder_JetAuto/pi3/log \
  build \
  --symlink-install \
  --build-base /root/build/HiWonder_JetAuto/pi3/build \
  --install-base /root/build/HiWonder_JetAuto/pi3/install \
  --cmake-args "-DCMAKE_C_COMPILER=/usr/bin/gcc" "-DCMAKE_CXX_COMPILER=/usr/bin/g++"
# 注: --cmake-args 是因为 /usr/local/bin/cc (Claude Code) 占用了 cc 命令名
#     导致 CMake 会找到 cc 脚本而非真正的 gcc，必须显式指定编译器
```

## 部署到目标设备
```bash
# Pi3
scp -r /root/build/HiWonder_JetAuto/pi3/install pi@<pi3-ip>:/home/pi/pi3_ws/

# Jetson
scp -r /root/build/HiWonder_JetAuto/jetson/install nvidia@<jetson-ip>:/home/nvidia/jetson_ws/
```

## 在目标设备上运行
```bash
# Pi3
cd ~/pi3_ws && source install/setup.bash
./pi3_start.sh

# Jetson (SLAM 建图 - ssh 后台)
cd ~/jetson_ws && source install/setup.bash
./jetson_start.sh

# Jetson (桌面 SLAM)
./jetson_slam.sh

# Jetson (键盘控制)
./jetson_teleop.sh

# Jetson (导航)
./jetson_navigation.sh

# 舵机控制
ros2 run jetauto_peripherals servo_control <servo_id> <position>
```

## 启动脚本汇总 (jetson/)
| 脚本 | 用途 | 环境 |
|------|------|------|
| `jetson_start.sh` | SLAM 建图 (无界面, ssh 友好) | 后台 |
| `jetson_slam.sh` | SLAM 建图 + RViz | 桌面 |
| `jetson_navigation.sh` | Nav2 导航 | 桌面/ssh |
| `jetson_rviz.sh` | 独立 RViz 可视化 | 桌面 |
| `jetson_teleop.sh` | 键盘控制小车 | 终端 |

## ROS 依赖
### Pi3 侧
- `rclpy/rclcpp`, `sensor_msgs`, `geometry_msgs`, `nav_msgs`, `tf2`
- `robot_state_publisher`, `joint_state_publisher`, `urdf/xacro`
- 系统: `libeigen3-dev`, `libyaml-cpp-dev`

### Jetson 侧 (额外)
- `slam_toolbox`, `laser_filters`, `rtabmap_slam`
- `nav2_bringup`, `nav2_planner`, `nav2_navigation`
- `cv_bridge`, `image_transport`, `camera_info_manager`
- `message_filters`, `tf2_sensor_msgs`
- `astra_camera` 为源码包 (Git submodule in `orbbec_ws/`)

## 注意事项
- 双机通过 ROS_DOMAIN_ID=42 通信
- orbbec_ws 为 Git submodule，clone 后需要 `git submodule update --init`
- Jetson 启动脚本假设在 `~/jetson_ws/` 下执行
- Pi3 启动脚本假设在 `~/pi3_ws/` 下执行

## 每日收尾流程
每天工作结束时执行：
```bash
# 1. 查看当天 git 变更
cd /workspace/HiWonder_JetAuto
git diff --stat

# 2. 确定新版本号 (当前最大版本 + 0.0.1)
#    查看当前版本: ls Changelog/ | sort -V | tail -1

# 3. 更新 Changelog/0.x.x.md
#    格式: "# 版本号" → 更新内容(模块分类) → 具体变更点

# 4. 提交推送
git add -A
git commit -m "chore: release 0.9.7"
git push
```
