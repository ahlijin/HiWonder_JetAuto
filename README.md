# HiWonder JetAuto：Pi3 + Jetson 双机版

这个仓库基于幻尔 JetAuto 的思路，整理成 **树莓派 3（Pi3）负责底层控制**、**Jetson 负责感知 / SLAM / 导航 / AI** 的双机协同结构。

当前原则：

- `pi3/` 侧代码以**已在实际环境跑通过**的内容为主，尽量少改。
- `jetson/` 侧代码用于承接计算密集型任务，可以按实际硬件情况持续调整。

---

## 目录结构

```text
.
├─ pi3/
│  ├─ pi3_start.sh
│  └─ src/
├─ jetson/
│  ├─ jetson_start.sh
│  ├─ jetson_slam.sh
│  ├─ jetson_navigation.sh
│  ├─ jetson_rviz.sh
│  └─ src/
└─ README.md
```

---

## 总体分工

### Pi3：底层控制与传感器接入

Pi3 侧主要负责：

- 底盘控制
- 舵机 / 控制板通信
- 激光雷达接入
- 机器人描述与基础外设
- 为 Jetson 提供稳定的 `/scan`、`/odom`、底盘控制接口等

### Jetson：计算与上层能力

Jetson 侧主要负责：

- 深度相机接入
- SLAM
- 导航
- 语音
- 目标检测 / 视觉 AI
- 需要较强算力的融合和可视化任务

---

## `pi3/` 目录说明

`pi3/` 是**底层稳定基线**，当前尽量作为参考实现保留。

### 启动脚本

- `pi3/pi3_start.sh`
  - Pi3 侧统一启动入口。

### 主要功能包

- `pi3/src/bringup/`
  - Pi3 端整体启动组织。
- `pi3/src/controller/`
  - 底盘控制相关节点与配置。
- `pi3/src/driver/`
  - 底层驱动封装。
- `pi3/src/ros_robot_controller/`
  - 机器人控制板相关节点。
- `pi3/src/peripherals/`
  - Pi3 侧外设支持。
- `pi3/src/lidar_bridge/`
  - 激光雷达桥接相关功能。
- `pi3/src/sllidar_ros2/`
  - 思岚雷达 ROS2 驱动，来自 git submodule。
- `pi3/src/jetauto_description/`
  - 机器人模型、URDF、RViz 配置。
- `pi3/src/servo_controller/`
  - 舵机控制。
- `pi3/src/interfaces/`
  - 自定义消息 / 服务定义。

### Pi3 侧特点

- 更偏向真实硬件驱动与稳定运行。
- 建议优先保证这一侧话题和控制链路稳定。
- 如果 Jetson 侧有问题，优先避免反向影响 Pi3 基线。

---

## `jetson/` 目录说明

`jetson/` 是**上层计算工作区**，负责把 Pi3 提供的底层能力接到 SLAM、导航、视觉与语音模块中。

### 启动脚本

- `jetson/jetson_start.sh`
  - Jetson 总启动入口。
- `jetson/jetson_slam.sh`
  - SLAM 相关启动。
- `jetson/jetson_navigation.sh`
  - 导航相关启动。
- `jetson/jetson_rviz.sh`
  - RViz 可视化启动。

### 主要功能包

- `jetson/src/peripherals/`
  - Jetson 侧外设支持，当前重点包括深度相机 launch。
- `jetson/src/slam/`
  - SLAM 相关 launch、配置与地图文件。
- `jetson/src/navigation/`
  - 导航相关节点、配置和 RViz。
- `jetson/src/lidar_receiver/`
  - 接收 / 转发雷达数据，衔接 Pi3 与 Jetson。
- `jetson/src/yolov5_ros2/`
  - 视觉检测相关功能。
- `jetson/src/xf_mic_asr_offline/`
  - 离线语音相关能力。
- `jetson/src/interfaces/`
  - Jetson 侧共用消息 / 服务定义。

### Jetson 侧当前注意事项

当前 Astra Pro 在 Jetson 这套环境里已经验证到以下情况：

- 深度 profile 需要使用设备实际支持的组合，不能直接照搬官方默认值。
- 彩色流在当前 **Astra Pro + USB2.0 + Jetson + 现有驱动** 组合下不稳定。
- 因此当前代码里采用了**保守策略**：
  - 优先保证 Jetson 默认链路可稳定启动；
  - 默认不强依赖彩色流；
  - 彩色作为可选项继续单独调试。

---

## 双机通信建议

建议 Jetson 与 Pi3：

- 使用有线网络直连或同一局域网稳定连接。
- 统一 ROS2 发行版（当前仓库按 **ROS2 Humble** 组织）。
- 保持一致的网络发现配置与环境变量。

实际使用时推荐：

1. 先确认 Pi3 侧底层节点正常；
2. 再启动 Jetson 侧 SLAM / 导航 / 可视化；
3. 最后再按需增加视觉、语音等附加模块。

---

## 推荐启动顺序

### 1. 启动 Pi3

```bash
cd ~/HiWonder_JetAuto/pi3
bash pi3_start.sh
```

### 2. 启动 Jetson 基础能力

```bash
cd ~/HiWonder_JetAuto/jetson
bash jetson_start.sh
```

### 3. 按需启动 SLAM / 导航 / RViz

```bash
bash jetson_slam.sh
bash jetson_navigation.sh
bash jetson_rviz.sh
```

> 具体脚本内容和依赖环境以本机工作区配置为准。

---

## 开发约定

为了避免双机系统被不必要的改动破坏，建议遵循：

1. **优先不动 `pi3/`**
   - Pi3 侧已经更接近“已验证稳定版”。
2. **Jetson 侧先保守可用，再逐步增强**
   - 先保证能跑，再逐步加彩色相机、视觉检测、语音等。
3. **修改 launch 时优先考虑真实硬件能力**
   - 特别是相机分辨率、帧率、格式，不要只参考官方默认值。
4. **把底层链路和上层算法解耦**
   - 即使相机或 AI 模块异常，也尽量不要拖垮底盘、雷达和基础导航链路。

---

## 当前仓库状态说明

- `pi3/`：作为底层稳定参考实现。
- `jetson/`：持续整理和适配中。
- `README.md`：按当前仓库实际目录和双机职责重新整理。

如果后面继续迭代，建议优先补充：

- Jetson / Pi3 各自的环境初始化步骤；
- 双机 ROS2 网络配置示例；
- 常用启动命令与故障排查记录；
- 话题、TF、节点依赖关系图。