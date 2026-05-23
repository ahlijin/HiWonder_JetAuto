# HiWonder JetAuto：Pi3 + Jetson 双机版

这是一个基于 HiWonder JetAuto 思路整理的 **Pi3 + Jetson 双机协同 ROS2 项目**。

- **Pi3** 负责底层控制、基础传感器与硬件接口
- **Jetson** 负责感知、SLAM、导航以及更高算力需求的功能

项目目标是把底层运动控制与上层算法能力拆分到两台设备上，形成更清晰、稳定的系统结构。

---

## 项目框架

### 总体分工

#### Pi3：底层控制层

Pi3 侧主要承担机器人运行所需的基础能力：

- 底盘控制（Mecanum 轮运动学 + 里程计）
- 舵机与控制板通信（转向舵机）
- IMU / 按键 / 电池等基础状态采集
- 激光雷达接入与转发
- 机器人模型描述与 TF 发布
- 接收手柄 / 键盘 / 来自 Jetson 的 `/cmd_vel` 控制指令
- 对上提供 `/scan`、`/odom`、控制接口等底层能力

#### Jetson：上层计算层

Jetson 侧主要承担计算密集型和感知决策类任务：

- 激光雷达数据接收与滤波
- 深度相机接入
- 激光 SLAM 建图与定位
- 导航与路径规划
- RViz 可视化
- 键盘控制小车移动（Jetson 侧遥操作）
- 舵机转向控制
- 视觉检测 / 语音等扩展能力

---

## 目录结构

```text
.
├─ pi3/
│  ├─ pi3_start.sh
│  ├─ src/
│  └─ doc/
├─ jetson/
│  ├─ jetson_start.sh          # 无界面 SLAM 启动（ssh 用）
│  ├─ jetson_slam.sh           # 桌面 SLAM 启动（含 RViz + 地图保存）
│  ├─ jetson_navigation.sh     # 导航启动
│  ├─ jetson_rviz.sh           # 独立 RViz 启动
│  ├─ jetson_teleop.sh         # Jetson 侧键盘控制
│  └─ src/
├─ Changelog/
│  ├─ 0.9.0.md
│  ├─ 0.9.1.md
│  ├─ 0.9.2.md
│  ├─ 0.9.3.md
│  ├─ 0.9.4.md
│  ├─ 0.9.5.md
│  └─ 0.9.6.md
└─ README.md

---

## 功能说明

### Pi3 侧功能

`pi3/` 用作机器人底层能力工作区，重点是稳定驱动与硬件控制，主要包括：

- `bringup/`：Pi3 侧整体启动组织
- `controller/`：底盘控制（Mecanum 运动学、里程计发布）
- `ros_robot_controller/`：控制板通信与状态收发（电机、舵机、IMU、按键）
- `sllidar_ros2/`：激光雷达 ROS2 驱动
- `jetauto_description/`：机器人模型、URDF、STL 模型文件
- `servo_controller/`：舵机控制器（转向舵机管理）
- `interfaces/`、`ros_robot_controller_msgs/`：消息与服务定义
- `calibration/`、`imu_calib/`：标定与调试相关功能
- `peripherals/`：外设支持（手柄控制、键盘控制、IMU TF 广播）

Pi3 侧的核心定位是：

- 提供稳定的运动与传感器基础接口
- 尽量减少对高层算法的依赖
- 作为双机系统中的硬件控制基线

### Jetson 侧功能

`jetson/` 用作上层计算工作区，负责接入 Pi3 的底层数据并实现更复杂的功能，主要包括：

- `jetauto_peripherals/`：Jetson 侧外设接入（深度相机 launch、键盘遥控、舵机控制）
- `slam/`：SLAM 启动、配置、建图相关资源
- `navigation/`：导航、定位、参数与可视化配置
- `orbbec_ws/`：Orbbec 深度相机驱动（Git submodule）
- `interfaces/`、`ros_robot_controller_msgs/`：复用的接口定义

Jetson 侧当前重点能力包括：

- 接收并利用 Pi3 提供的基础状态与雷达数据
- 使用激光雷达 + SLAM Toolbox 完成建图
- 键盘控制小车移动、舵机转向控制
- 深度相机环境感知
- 导航与路径规划
- 提供 RViz 可视化与上层扩展能力

---

## 双机协同方式

本项目采用双机分层架构：

1. **Pi3 负责底层实时控制与基础传感器接入**
2. **Jetson 负责高层感知、建图、导航与扩展功能**
3. 两侧通过统一的 ROS2 通信环境（`ROS_DOMAIN_ID=42`）协同工作

这样的结构有几个直接好处：

- 降低上层算法变化对底层控制稳定性的影响
- 让高算力任务集中在 Jetson 侧执行
- 保持底层控制链路和上层感知链路职责清晰

---

## 启动方式

### Pi3 启动

```bash
cd ~/pi3_ws
./pi3_start.sh
```

### Jetson 启动

```bash
cd ~/jetson_ws

# SLAM 建图（后台，适合 ssh）
./jetson_start.sh

# SLAM 建图（桌面，含 RViz）
./jetson_slam.sh

# 键盘控制小车移动
./jetson_teleop.sh

# 舵机控制
ros2 run jetauto_peripherals servo_control <servo_id> <position>

# 导航
./jetson_navigation.sh
```

---

## ROS 依赖库

### Pi3 侧依赖

以下为 Pi3 侧 `apt` 安装的 ROS 依赖包：

| 包名 | 用途 |
|------|------|
| `rclpy` / `rclcpp` | ROS2 Python / C++ 客户端库 |
| `sensor_msgs` | 传感器消息类型（LaserScan、Imu 等） |
| `std_msgs` / `std_srvs` | 标准消息与服务 |
| `geometry_msgs` | 几何消息类型（Pose、Twist 等） |
| `nav_msgs` | 导航消息类型（Odometry 等） |
| `tf2` / `tf2_msgs` / `tf2_ros` | TF 坐标系变换 |
| `robot_state_publisher` | 发布机器人模型 TF |
| `joint_state_publisher` | 关节状态发布 |
| `urdf` / `xacro` | URDF 模型解析与宏预处理 |
| `rosidl_default_generators` / `rosidl_default_runtime` | 消息/服务接口代码生成 |
| `launch` / `launch_ros` | Launch 启动框架 |
| `ament_index_python` | 包路径查找 |

系统级依赖：

| 包名 | 用途 |
|------|------|
| `libeigen3-dev` | 线性代数库（imu_calib） |
| `libyaml-cpp-dev` | YAML 解析库（imu_calib） |

### Jetson 侧依赖

Jetson 侧除 Pi3 侧大部分基础包外，额外需要：

| 包名 | 用途 |
|------|------|
| `slam_toolbox` | 激光 SLAM 建图与定位 |
| `laser_filters` | 激光雷达数据过滤（角度/距离滤波） |
| `rtabmap_slam` / `rtabmap_sync` | RTAB-Map 建图与 RGBD 同步 |
| `nav2_bringup` / `nav2_controller` | Nav2 导航框架 |
| `nav2_planner` / `nav2_navigation` | 导航规划与执行 |
| `nav2_bt_navigator` / `nav2_localization` | 行为树导航与定位 |
| `camera_info_manager` | 相机信息管理 |
| `cv_bridge` | ROS ↔ OpenCV 图像桥接 |
| `image_geometry` / `image_publisher` / `image_transport` | 图像处理与传输 |
| `rclcpp_components` | 组件节点加载 |
| `class_loader` | 动态类加载 |
| `message_filters` | 消息时间同步 |
| `tf2_sensor_msgs` | 传感器点云 TF 变换 |
| `control_msgs` | 轨迹控制消息（FollowJointTrajectory） |

> 注：`astra_camera`（Orbbec 深度相机驱动）为源码包，通过 Git submodule 引入，
> 位于 `jetson/src/orbbec_ws/`，非 `apt` 安装。

---

## 当前能力概览

当前仓库围绕以下方向组织：

- 双机 ROS2 协同
- 底盘与舵机控制
- 激光雷达接入与滤波
- 深度相机接入
- 机器人模型与描述
- SLAM 建图
- 导航与定位
- Jetson 侧键盘控制与舵机遥控
- RViz 可视化
- 视觉 AI 扩展
- 语音功能扩展

更新日志请查看：

- `Changelog/0.9.0.md`
- `Changelog/0.9.1.md`
- `Changelog/0.9.2.md`
- `Changelog/0.9.3.md`
- `Changelog/0.9.4.md`
- `Changelog/0.9.5.md`
- `Changelog/0.9.6.md`
