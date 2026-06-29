# HiWonder_JetAuto — Pi3 底层控制 ROS2 项目

基于 HiWonder JetAuto 的 Pi3 侧 ROS2 工作空间。
负责电机驱动、舵机控制、LiDAR、IMU、里程计等底层硬件。

> Jetson 侧代码已迁移至 [HiJetson](https://github.com/ahlijin/HiJetson) 仓库的 `lite` 分支。

## 硬件分工
| 设备 | 职责 |
|------|------|
| **Pi3** (底层控制层) | 底盘控制 (Mecanum)、舵机、IMU/按键/电池采集、LiDAR 接入、模型描述/TF、cmd_vel 接收 |

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
└── Changelog/                        # 版本日志
```

## 编码规范
- **语言**: Python 3.10 (大多数节点), C++ (imu_calib)
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
```

## 部署到 Pi3
```bash
scp -r /root/build/HiWonder_JetAuto/pi3/install pi@<pi3-ip>:/home/pi/pi3_ws/
```

## 在 Pi3 上运行
```bash
cd ~/pi3_ws && source install/setup.bash
./pi3_start.sh
```

## ROS 依赖
- `rclpy/rclcpp`, `sensor_msgs`, `geometry_msgs`, `nav_msgs`, `tf2`
- `robot_state_publisher`, `joint_state_publisher`, `urdf/xacro`
- 系统: `libeigen3-dev`, `libyaml-cpp-dev`

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
