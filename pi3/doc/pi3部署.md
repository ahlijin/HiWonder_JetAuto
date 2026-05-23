

---

## 📋 树莓派3 Pi3 部署指南（Ubuntu 22.04 Server）

### 1. 添加 ROS2 Humble 源
- **命令**：
  ```bash
  sudo apt install -y curl
  sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg
  echo "deb [signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] https://mirrors.ustc.edu.cn/ros2/ubuntu jammy main" | sudo tee /etc/apt/sources.list.d/ros2.list
  sudo apt update
  ```

### 2. 安装 ROS2 Humble 最小系统 + 依赖库
- **目的**：只装需要的包，Pi3 资源有限，不装 RViz/Gazebo 等 GUI 工具。
- **命令**：
  ```bash
  sudo apt install -y ros-humble-ros-base \
    ros-humble-rclpy \
    ros-humble-rclcpp \
    ros-humble-std-msgs \
    ros-humble-std-srvs \
    ros-humble-sensor-msgs \
    ros-humble-geometry-msgs \
    ros-humble-nav-msgs \
    ros-humble-tf2 \
    ros-humble-tf2-msgs \
    ros-humble-tf2-ros \
    ros-humble-robot-state-publisher \
    ros-humble-joint-state-publisher \
    ros-humble-urdf \
    ros-humble-xacro \
    ros-humble-launch \
    ros-humble-launch-ros \
    ros-humble-ament-index-python \
    ros-humble-rosidl-default-generators \
    ros-humble-rosidl-default-runtime \
    ros-humble-builtin-interfaces \
    libeigen3-dev \
    libyaml-cpp-dev \
    python3-serial
  ```

### 3. 配置 ROS 环境
- **添加到 `~/.bashrc`**：
  ```bash
  echo 'source /opt/ros/humble/setup.bash' >> ~/.bashrc
  echo 'export ROS_DOMAIN_ID=42' >> ~/.bashrc
  source ~/.bashrc
  ```

### 4. 配置 udev 规则（固定 USB 设备名）
- **目的**：让雷达固定为 `/dev/lidar`，控制板固定为 `/dev/rrc`，不随 USB 插口变化。
- **命令**：
  ```bash
  cd ~/pi3_ws/..
  ./create_udev_rules.sh
  ```
- **重新插拔雷达与控制板的 USB 线**，验证：
  ```bash
  ls -la /dev/lidar /dev/rrc
  ```

### 5. 确认设备映射
| 设备 | USB ID | 映射为 |
|------|--------|--------|
| 激光雷达（A1/A2） | `1a86:7523` | `/dev/lidar` |
| 控制板 | `1a86:55d4` | `/dev/rrc` |

- 如果雷达的芯片型号不同，修改 `lidar.rules` 中的 `idVendor` 和 `idProduct`，重新执行 `create_udev_rules.sh`。

### 6. 启动测试
- **首次启动**：
  ```bash
  cd ~/pi3_ws
  ./pi3_start.sh
  ```
- **观察日志**，确认以下节点正常运行：
  - `ros_robot_controller`：控制板通信
  - `sllidar_node`：激光雷达数据
  - `odom_publisher`：里程计发布
  - `servo_manager / controller_manager`：舵机控制
  - `joystick_control`：手柄控制
  - `joint_state_publisher`：关节状态
  - `startup_check`：启动蜂鸣

---

## ✅ 验证清单
- [ ] 雷达：`ls -la /dev/lidar` 存在，`ros2 topic echo /scan_raw` 有数据
- [ ] 控制板：`ls -la /dev/rrc` 存在，`ros2 topic echo /ros_robot_controller/imu` 有数据
- [ ] 里程计：`ros2 topic echo /odom` 有数据
- [ ] Jetson 可订阅到 Pi3 的话题（`ROS_DOMAIN_ID=42` 需一致）

---
