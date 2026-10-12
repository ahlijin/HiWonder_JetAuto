

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

---

## 🔧 编译与部署（最新流程 2026-08）

### 编译（开发机 = 宿主机 Pi5 的 my-ros 容器）

> 编译环境是宿主机(Pi5)上的 docker 容器 `my-ros`(ROS2 humble + colcon, aarch64)。
> 源码取自本地 clone (gitea), 直接挂载; 编译产物输出到宿主机本地目录。

```bash
docker run --rm \
  -v /home/pi/hermes-data/code/HiWonder_JetAuto/pi3:/ws \
  -v /home/pi/hermes-data/pi3build:/out \
  my-ros bash -c 'source /opt/ros/humble/setup.bash && cd /ws/src && \
  colcon --log-base /out/log build --build-base /out/build --install-base /out/install'
```

**要点:**
- `docker -v` 挂载的是**宿主机路径**(Hermes 容器内 `/opt/data` 即宿主机 `/home/pi/hermes-data`), 不是容器内 /workspace
- 源码只读挂载; 产物输出到 /out(=宿主机本地目录)
- **不能用 --symlink-install**: 部署靠 scp, 软连接会失效
- 架构必须与 Pi3 一致(aarch64)

### 部署（install → Pi3）

```bash
# 编译产物在 Hermes 容器 /opt/data/pi3build/install
scp -r /tmp/pi3_install pi@192.168.3.64:~/pi3_ws/
```

**注意**: `scp -r 目录 host:~/pi3_ws/` 当目标目录已存在时, 会创建 `~/pi3_ws/pi3_install`
而**不是**合并进 `~/pi3_ws/install`。正确替换:

```bash
mv ~/pi3_ws/install ~/pi3_ws/install.old
mv ~/pi3_ws/pi3_install ~/pi3_ws/install
```

确认新代码生效后删掉 `install.old`。

### 舵机控制要点

- 总线舵机脉冲范围 **0-1000(中心 500)**, 机械限位 ±45° = **312-688**
- `controller_manager` 对上游所有 pulse 指令**硬限幅 312-688** (含手柄/语音/Jetson 直通路径)
- **已知修复**: 上游若发 int 类型 position, rosidl 断言(position 必须 float)会抛
  AssertionError 导致 controller_manager 进程崩溃、舵机链路全断 — 已加 `float()` 防御
- 启动后确认 `controller_manager` 进程在跑: `ps aux | grep controller_manager`
  (bringup 里它若崩溃不会被自动拉起, 表现为"手柄/语音都控不了舵机")

---

## 📝 变更记录

- **2026-08-04 (v0.10.0)**: 全向碰撞检测（前/左/右三扇区，旋转按转向侧 STOP 0.15m / SLOW 0.30m）；旋转堵转检测（IMU 角速度 <0.08rad/s 持续 1s → 停车+蜂鸣，参数 stall_angular_threshold/stall_detect_time/safety_side_angle）；app_cmd_vel angular 限幅 0.5→0.6
- **2026-08-01**: controller_manager float() 防御(修 int position 崩溃); 舵机脉冲硬限幅 312-688
- **2026-07-29 (v0.9.9)**: 舵机限幅 ±45°、LiDAR 防撞保护、pi3_stop.sh
