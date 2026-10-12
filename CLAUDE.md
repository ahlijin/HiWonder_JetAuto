# HiWonder_JetAuto — Pi3 底层控制 ROS2 项目

基于 HiWonder JetAuto 的 Pi3 侧 ROS2 工作空间。
负责电机驱动、舵机控制、LiDAR、IMU、里程计等底层硬件。

> Jetson 侧代码已迁移至 [HiJetson](http://192.168.3.96:3000/legend/HiJetson) 仓库（单板早期版本见其 `lite` 分支）。

## 仓库
- origin: ssh://git@192.168.3.96:2222/legend/HiWonder_JetAuto.git（Web/API 同机 http://192.168.3.96:3000/legend/HiWonder_JetAuto；NAS 与 github 在线仓库已弃用）
- 本地 clone: `/workspace/HiWonder_JetAuto`（Pi5 宿主 `/home/pi/workspace/HiWonder_JetAuto`）
- 子模块 `src/sllidar_ros2` = legend/sllidar_ros2（gitea 镜像，只读，pin `34300099`）
- CI: 推送自动编译 `.gitea/workflows/build.yml`（gitea-runner，runs-on pi5，容器 `my-ros:latest`）

## 硬件分工
| 设备 | 职责 |
|------|------|
| **Pi3** (底层控制层) | 底盘控制 (Mecanum)、舵机、IMU/按键/电池采集、LiDAR 接入、模型描述/TF、cmd_vel 接收 |

## 项目结构
```
HiWonder_JetAuto/
├── src/                              # ROS2 工作空间 (11 个包, 直接在仓库根)
│   ├── bringup/                      # 整体启动
│   ├── controller/                   # 底盘控制 (Mecanum 运动学 + 里程计)
│   ├── ros_robot_controller/         # 控制板通信 (电机/舵机/IMU/按键)
│   ├── sllidar_ros2/                 # 激光雷达驱动 (Git submodule)
│   ├── jetauto_description/          # URDF 模型 + STL
│   ├── servo_controller/             # 舵机控制
│   ├── calibration/                  # 标定相关
│   ├── imu_calib/                    # IMU 标定 (C++, Eigen)
│   ├── peripherals/                  # 手柄/键盘/IMU TF
│   ├── ros_robot_controller_msgs/    # 控制板消息定义
│   └── interfaces/                   # 消息与服务定义
├── scripts/                          # pi3_start.sh / pi3_stop.sh / udev 规则与安装脚本
├── doc/                              # 部署指南与系统优化文档
├── .gitea/workflows/build.yml        # CI: 推送自动编译
└── Changelog/                        # 版本日志
```

## 编码规范
- **语言**: Python 3.10 (大多数节点), C++ (imu_calib)
- **ROS2**: Humble, ROS_DOMAIN_ID=42
- **Python 风格**: PEP 8, 4空格缩进
- **Shell 脚本**: 头部含注释说明, set -e 错误处理
- **YAML 配置**: 2空格缩进

## 构建

### 方式一：CI（推送自动编译，只验证能不能编过）
```bash
git push     # → .gitea/workflows/build.yml → gitea-runner(runs-on pi5) → 容器 my-ros:latest 跑 colcon build
```
产物在 runner 那台的 `/home/pi/runner-data/ws`（runner 容器内 `/data/ws`），不上传 artifact；结果看 Gitea Actions 页。

### 方式二：开发机（Pi5 宿主）my-ros 容器（开发迭代用，2026-10 实测可用）
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
# 工作空间根就是 /ws (目录扁平化后 src/ 在仓库根, 不再 cd /ws/src)
```

### 方式三：部署到 Pi3（不带 symlink）
部署包不含 symlink（symlink 指向本地路径，scp 到 Pi3 后失效），需用**另一个产物目录**重编一次：
```bash
docker run --rm \
  -v /home/pi/workspace/HiWonder_JetAuto:/ws \
  -v /home/pi/hermes-data/pi3build_deploy:/out \
  -w /ws \
  my-ros:latest \
  bash -c 'source /opt/ros/humble/setup.bash && \
    colcon --log-base /out/log build --build-base /out/build --install-base /out/install'

# 产物在宿主机 /home/pi/hermes-data/pi3build_deploy/install (Hermes 容器 /opt/data/pi3build_deploy/install)
scp -r /home/pi/hermes-data/pi3build_deploy/install pi@192.168.3.64:~/pi3_ws/pi3_install
# scp 目录到已存在的 ~/pi3_ws/ 会生成 pi3_ws/pi3_install, 需手动 mv 成 install (见 doc/pi3部署.md)
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
./pi3_start.sh          # 仓库里的副本: scripts/pi3_start.sh, 改动后需 scp 到 Pi3 的 ~/pi3_ws/
                      # 停止: scripts/pi3_stop.sh (pkill 全部节点)
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
