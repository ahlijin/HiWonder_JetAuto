# HiWonder JetAuto：Pi3 底盘控制（双机方案的底层）

这是一个基于 HiWonder JetAuto 思路整理的 **Pi3 + Jetson 双机协同 ROS2 项目**，本仓库现在**只保留 Pi3 侧（底层控制）**。

- **Pi3**（本仓库）：底盘运动控制（Mecanum 轮运动学 + 里程计）、舵机、控制板通信（电机 / IMU / 按键 / 电池）、激光雷达接入、机器人模型与 TF、接收上层 `/cmd_vel` 指令
- **Jetson**（姊妹仓库 [HiJetson](http://192.168.3.96:3000/legend/HiJetson)）：感知、语音、SLAM、导航、RViz 可视化等上层能力

> 历史上这里是"Pi3 + Jetson 双机"仓库（含 `jetson/` 目录）。`jetson/` 已于 0.9.7 移除，
> Jetson 侧代码迁至 **HiJetson** 仓库（早期单板版本保留在其 `lite` 分支）。

## 硬件分工

| 设备 | 职责 |
|------|------|
| **Pi3**（底层控制层） | 底盘控制 (Mecanum)、总线舵机、IMU / 按键 / 电池采集、LiDAR 接入、模型描述 / TF、接收 `cmd_vel` |
| **Jetson**（上层计算层） | 深度相机、语音交互、激光 SLAM 建图定位、Nav2 导航、RViz、唤醒后整车旋转等感知决策类任务 |

两侧通过同一 ROS2 DDS 环境协同（`ROS_DOMAIN_ID=42`），无需额外中间件。

## 目录结构

```text
.
├─ src/                          # ROS2 工作空间源码（11 个包，直接在仓库根）
│  ├─ bringup/                   # Pi3 整体启动（startup_check 等）
│  ├─ controller/                # 底盘控制：Mecanum 运动学 + 里程计（odom_publisher_node）
│  ├─ ros_robot_controller/      # 控制板通信（电机 / 舵机 / IMU / 按键 / 电池）
│  ├─ ros_robot_controller_msgs/
│  ├─ servo_controller/          # 总线舵机控制（controller_manager / bus_servo_control）
│  ├─ sllidar_ros2/              # 激光雷达驱动（Git submodule → legend/sllidar_ros2）
│  ├─ jetauto_description/       # URDF 模型 + STL + RViz 配置
│  ├─ peripherals/               # 手柄 / 键盘遥控（含 sllidar_a1.launch.py）
│  ├─ calibration/               # 线速度 / 角速度标定
│  ├─ imu_calib/                 # IMU 标定（C++，Eigen）
│  └─ interfaces/                # 自定义消息与服务定义
├─ scripts/                      # pi3_start.sh / pi3_stop.sh / udev 规则与安装脚本
├─ doc/                          # pi3部署.md / ubuntu22.04.5系统优化.md
├─ .gitea/workflows/             # CI: deploy-pi3.yml（推送 main 编译+部署）/ release.yml（打 tag 出 Release）
├─ Changelog/                    # 版本日志（最新 0.10.1）
├─ CLAUDE.md                     # CC 项目上下文
└─ README.md
```

> 目录已扁平化（0.9.10 起）：原 `pi3/src`、`pi3/scripts`、`pi3/doc` 上移为仓库根的 `src/`、`scripts/`、`doc/`。

## Pi3 侧功能说明

- `bringup/`：Pi3 整体启动编排（`pi3_bringup.launch.py`、`startup_check` 开机自检 + 提示音）
- `controller/`：底盘控制核心 —— Mecanum 运动学解算、里程计发布、碰撞/堵转保护（`odom_publisher_node.py`）
- `ros_robot_controller/`：与 STM32 控制板串口通信，收发电机、总线舵机、IMU、按键、电池、蜂鸣器、LED
- `servo_controller/`：总线舵机管理（`controller_manager` 接收 `ServosPosition` 并下发到控制板，回发 `joint_states` / `servo_states`）
- `sllidar_ros2/`：A1 激光雷达 ROS2 驱动（发布 `/scan`）
- `jetauto_description/`：机器人 URDF/STL 与 TF
- `peripherals/`：手柄（`joystick_control`）与键盘（`teleop_key_control`）遥控
- `calibration/`、`imu_calib/`：线/角速度标定与 IMU 标定

## 接口一览（Pi3 侧）

| Topic | 类型 | 方向 | 说明 |
|-------|------|------|------|
| `/cmd_vel` | Twist | **Jetson → Pi3** | 上层速度指令（语音、唤醒旋转、导航） |
| `/controller/cmd_vel` | Twist | 本地 → Pi3 | 手柄 / 键盘 / 标定脚本的本地指令 |
| `/servo_controller` | ServosPosition | **Jetson → Pi3** | 总线舵机脉冲指令（限幅 312-688，±45°） |
| `/odom` | Odometry | Pi3 → 上层 | 里程计 |
| `/scan` | LaserScan | Pi3 → 上层 | 激光雷达（驱动发布，底盘侧也订阅 `scan_raw` 做碰撞检测） |
| `/ros_robot_controller/imu_raw` | Imu | Pi3 内部 | IMU 原始数据（旋转堵转检测用） |
| `/ros_robot_controller/set_motor` | MotorsState | Pi3 内部 | 电机指令 |
| `/ros_robot_controller/bus_servo/set_position` | ServosPosition | Pi3 内部 | 总线舵机下发 |
| `/ros_robot_controller/set_buzzer` | BuzzerState | 双向 | 蜂鸣器（开机提示音 / 堵转报警） |
| `/set_pose`、`/set_odom` | PoseWithCovarianceStamped / Pose2D | — | 位姿重置 / 里程计重置 |

## 最新能力（v0.10.0）

- **全向碰撞检测**（`odom_publisher_node.py`）
  - 三扇区距离：前方（π±30°）、左侧（90°±30°）、右侧（270°±30°）
  - 旋转时只查转向侧（左转查左、右转查右），另一侧不误伤
  - 0.15 m 停转 / 0.30 m 减速，与前进碰撞同阈值逻辑；参数 `safety_side_angle`（默认 30°）
- **旋转堵转检测**（麦轮被卡/打滑）
  - 订阅 IMU 角速度 z，旋转指令下持续 < `stall_angular_threshold`(0.08 rad/s) 达 `stall_detect_time`(1.0 s) → 停车 + 蜂鸣
  - 20 Hz 轮询，无旋转指令时不检测
- 此前修复：总线舵机脉冲**硬限幅 312-688**（物理 ±45°）、`controller_manager` int/float 防御、开机提示音 DDS 异步写丢失、舵机使能
- `angular` 限幅 0.5 → **0.6**（配合 Jetson 侧 `rotate_gain=0.6`，唤醒整车旋转速度加倍）

## 构建

**方式一：推送自动编译 + 部署到 Pi3（CI，2026-10 起）**

```bash
git push                    # main 分支 → .gitea/workflows/deploy-pi3.yml → gitea-runner(runs-on pi5)
                            #  1) my-ros:latest 容器里 colcon build
                            #  2) 打包 install + pi3_start.sh/pi3_stop.sh
                            #  3) ssh/scp 到 Pi3: 停节点 → 替换 ~/pi3_ws/install → 重启 pi3_start.sh
git push origin v0.10.2     # 打 tag → .gitea/workflows/release.yml → 建 Release + 上传 jetauto-vX.X.X.tar.gz
```

- 编译产物在 runner 那台的 `/home/pi/runner-data/ws`（runner 容器内 `/data/ws`），部署包由 CI 直接推到 Pi3（`pi@192.168.3.64`，runner 已配免密）
- 每次推送 main 都会**停掉 Pi3 上正在跑的节点再重启**：先把新包解到 `~/pi3_ws/.staging` 并校验，再 `pi3_stop.sh` → **原子替换** `install`（旧版本留成 `install.old`）→ `pi3_start.sh` → 校验 `~/pi3_ws/install/setup.bash` 与 `pi3_bringup` 进程；结果看 Gitea Actions 页
- 部署中途失败不影响设备（新包没落盘校验通过之前不动线上 `install`）；起不来的话回退一条命令：`ssh pi@192.168.3.64 "cd ~/pi3_ws && rm -rf install && mv install.old install && ./pi3_start.sh"`
- Release 资产为 `install/ + pi3_start.sh + pi3_stop.sh`，可用于手工部署
- 手工部署（CI 不通时）见方式二/三 + [doc/pi3部署.md](doc/pi3部署.md)

**方式二：开发机（Pi5 宿主）my-ros 容器里编（开发迭代用，实测可用）**

```bash
docker run --rm \
  -v /home/pi/workspace/HiWonder_JetAuto:/ws \
  -v /home/pi/hermes-data/pi3build:/out \
  -w /ws \
  my-ros:latest \
  bash -c 'source /opt/ros/humble/setup.bash && \
    colcon --log-base /out/log build --build-base /out/build --install-base /out/install'
# 实测: 11 packages finished [1m 24s]
# 挂载必须传宿主机路径: Hermes 容器内 /workspace = 宿主 /home/pi/workspace, /opt/data = 宿主 /home/pi/hermes-data
```

**方式三：在 Pi3 上原生编译（部署用，推荐，确保 ABI）**

```bash
source /opt/ros/humble/setup.bash
cd ~/pi3_ws
colcon build
# 部署不要用 --symlink-install（symlink 指向本机路径，scp 后失效）
```

## 运行

```bash
# Pi3 上
cd ~/pi3_ws && source install/setup.bash
./pi3_start.sh              # 内部: source ROS + install → ros2 launch bringup pi3_bringup.launch.py
```

启动脚本在仓库里的副本是 `scripts/pi3_start.sh`（`scripts/pi3_stop.sh` 停全部节点），CI 部署时会随 `install/` 一起同步到 Pi3 的 `~/pi3_ws/`。

`pi3_start.sh` 会设置 `ROS_DOMAIN_ID=42`，需与 Jetson 侧一致才能互通。

## ROS 依赖

| 包名 | 用途 |
|------|------|
| `rclpy` / `rclcpp` | ROS2 Python / C++ 客户端库 |
| `sensor_msgs` / `nav_msgs` / `geometry_msgs` / `std_msgs` / `std_srvs` | 消息类型 |
| `tf2` / `tf2_msgs` / `tf2_ros` | TF 坐标系变换 |
| `robot_state_publisher` / `joint_state_publisher` / `urdf` / `xacro` | 模型与关节状态 |
| `rosidl_default_generators` / `rosidl_default_runtime` | 自定义消息/服务代码生成 |
| `launch` / `launch_ros` / `ament_index_python` | Launch 框架 |
| `libeigen3-dev` / `libyaml-cpp-dev`（系统） | imu_calib 依赖 |
| `python3-serial`（系统） | 控制板串口通信 |

> 详细安装步骤（国内 ROS 源、依赖清单、udev 固定设备名 `/dev/lidar`、`/dev/rrc`）见 [doc/pi3部署.md](doc/pi3部署.md)。

## 注意

- `src/sllidar_ros2` 是 Git submodule，来源为本地 gitea 镜像 `legend/sllidar_ros2`（pin `34300099`）；用 `git clone --recurse-submodules` 或 `git submodule update --init --recursive` 拉取
- Jetson 侧代码不在本仓库，请访问 [HiJetson](http://192.168.3.96:3000/legend/HiJetson)（单板早期版本见其 `lite` 分支）

## 更新日志

见 [Changelog/](Changelog/) ，最新为 **0.10.1**（2026-10-12）。
