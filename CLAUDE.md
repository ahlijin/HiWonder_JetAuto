# HiWonder_JetAuto — Pi3 底层控制 ROS2 项目

基于 HiWonder JetAuto 的 Pi3 侧 ROS2 工作空间。
负责电机驱动、舵机控制、LiDAR、IMU、里程计等底层硬件。

> Jetson 侧代码已迁移至 [HiJetson](http://192.168.3.96:3000/legend/HiJetson) 仓库（单板早期版本见其 `lite` 分支）。

## 仓库
- origin: http://192.168.3.96:3000/legend/HiWonder_JetAuto.git （本地 gitea，NAS 与 github 在线仓库已弃用）
- 本地 clone: `/opt/data/code/HiWonder_JetAuto`（Pi5）
- 子模块 `pi3/src/sllidar_ros2` = legend/sllidar_ros2（gitea 镜像，只读）

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
│       ├── ros_robot_controller_msgs/ # 控制板消息定义
│       └── interfaces/              # 消息与服务定义
├── pi3/doc/                          # 部署指南与系统优化文档
└── Changelog/                        # 版本日志
```

## 编码规范
- **语言**: Python 3.10 (大多数节点), C++ (imu_calib)
- **ROS2**: Humble, ROS_DOMAIN_ID=42
- **Python 风格**: PEP 8, 4空格缩进
- **Shell 脚本**: 头部含注释说明, set -e 错误处理
- **YAML 配置**: 2空格缩进

## 构建

### 本地开发（Pi5，快速迭代）
```bash
source /opt/ros/humble/setup.bash

cd /opt/data/code/HiWonder_JetAuto/pi3
colcon \
  --log-base /opt/data/build/HiWonder_JetAuto/pi3/log \
  build \
  --symlink-install \
  --build-base /opt/data/build/HiWonder_JetAuto/pi3/build \
  --install-base /opt/data/build/HiWonder_JetAuto/pi3/install \
  --cmake-args "-DCMAKE_C_COMPILER=/usr/bin/gcc" "-DCMAKE_CXX_COMPILER=/usr/bin/g++"
```

### 部署到 Pi3（不带 symlink）
部署包不含 symlink（symlink 指向本地路径，scp 到 Pi3 后失效），需重新编译。
```bash
source /opt/ros/humble/setup.bash

cd /opt/data/code/HiWonder_JetAuto/pi3
colcon \
  --log-base /opt/data/build/HiWonder_JetAuto/pi3/build_deploy/log \
  build \
  --build-base /opt/data/build/HiWonder_JetAuto/pi3/build_deploy/build \
  --install-base /opt/data/build/HiWonder_JetAuto/pi3/build_deploy/install \
  --cmake-args "-DCMAKE_C_COMPILER=/usr/bin/gcc" "-DCMAKE_CXX_COMPILER=/usr/bin/g++"

scp -r /opt/data/build/HiWonder_JetAuto/pi3/build_deploy/install pi@<pi3-ip>:/home/pi/pi3_ws/
```

也可直接在 Pi3 上编译（推荐，确保原生 ABI）：
```bash
# Pi3 上
source /opt/ros/humble/setup.bash
cd ~/pi3_ws
colcon build
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
cd /opt/data/code/HiWonder_JetAuto
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
