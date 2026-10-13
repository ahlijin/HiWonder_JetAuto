

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
  cd <仓库>/scripts        # scripts/ 下同时放着 create_udev_rules.sh 和 *.rules
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

## 🔧 编译与部署（最新流程 2026-10）

### 编译（开发机 = 宿主机 Pi5 的 my-ros 容器）

> 编译环境是宿主机(Pi5)上的 docker 容器 `my-ros:latest`(ROS2 humble + colcon, aarch64)。
> 源码取自本地 clone (gitea, 现在在 `/workspace`), 直接挂载; 编译产物输出到宿主机本地目录。
> **CI（2026-10 起, 日常走这条)**: 推送 main → `.gitea/workflows/deploy-pi3.yml` 在 gitea-runner 里
> colcon build → 打包 `install + pi3_start.sh + pi3_stop.sh` → ssh/scp 到 Pi3(`pi@192.168.3.64`, runner 已配免密)
> → 停旧节点 → 替换 `~/pi3_ws/install` → 重启 `pi3_start.sh` → 校验 `install/setup.bash` 与 `pi3_bringup` 进程。
> 打 tag `v*` → `.gitea/workflows/release.yml` 建 Release 并上传 `jetauto-vX.X.X.tar.gz`(同样内容)。
> 下面的手工编译/部署只在 CI 不可用时用。

```bash
docker run --rm \
  -v /home/pi/workspace/HiWonder_JetAuto:/ws \
  -v /home/pi/hermes-data/pi3build:/out \
  -w /ws \
  my-ros:latest \
  bash -c 'source /opt/ros/humble/setup.bash && \
    colcon --log-base /out/log build --build-base /out/build --install-base /out/install'
# 实测 2026-10-12: 11 packages finished [1m 24s]
```

**要点:**
- `docker -v` 挂载的是**宿主机路径**: Hermes 容器中的 `/workspace` = 宿主 `/home/pi/workspace`(代码),
  Hermes 容器中的 `/opt/data` = 宿主 `/home/pi/hermes-data`(产物)
- 目录扁平化后源码就在仓库根的 `src/`(原 `pi3/src`), 所以**工作空间根 = `/ws`**, 不再 `cd /ws/src`
- 源码只读挂载; 产物输出到 /out(=宿主机本地目录)
- **不能用 --symlink-install**: 部署靠 scp, 软连接会失效
- 架构必须与 Pi3 一致(aarch64)

### 部署（install → Pi3）

#### 方式 A：CI 自动部署（推荐，2026-10 起）

`deploy-pi3.yml` 里跑的完整序列（无需 sudo，`~/pi3_ws` 属 pi）：

```bash
# 1. 传包 + 解到暂存目录（这步失败完全不影响设备: 旧代码还在跑）
scp jetauto-deploy.tar.gz pi@192.168.3.64:/tmp/
ssh pi@192.168.3.64 "rm -rf ~/pi3_ws/.staging && mkdir -p ~/pi3_ws/.staging"
ssh pi@192.168.3.64 "tar xzf /tmp/jetauto-deploy.tar.gz -C ~/pi3_ws/.staging && rm -f /tmp/jetauto-deploy.tar.gz"
ssh pi@192.168.3.64 "test -f ~/pi3_ws/.staging/install/setup.bash && test -f ~/pi3_ws/.staging/pi3_start.sh"   # 解包完整性校验
# 2. 停节点 → 原子换目录（mv 是同文件系统内的 rename, 不会出现"没有 install"的空窗; 旧版本留成 install.old）
ssh pi@192.168.3.64 "~/pi3_ws/pi3_stop.sh || true"
ssh pi@192.168.3.64 "cd ~/pi3_ws && rm -rf install.old && mv install install.old && mv .staging/install install \
  && mv -f .staging/pi3_start.sh .staging/pi3_stop.sh . && rm -rf .staging && chmod +x pi3_start.sh pi3_stop.sh"
# 3. 起节点 + 校验
ssh pi@192.168.3.64 "{ cd ~/pi3_ws && exec setsid nohup ./pi3_start.sh; } > ~/pi3_ws/pi3_run.log 2>&1 < /dev/null &"
ssh pi@192.168.3.64 "test -f ~/pi3_ws/install/setup.bash && pgrep -f 'pi3_[b]ringup'"
```

**回退**（新版本起不来时，一步退回上一份）：

```bash
ssh pi@192.168.3.64 "cd ~/pi3_ws && rm -rf install && mv install.old install && ./pi3_start.sh"
```

- 包内容 = `install/` + `pi3_start.sh` + `pi3_stop.sh`（`tar czf out.tar.gz -C ws install -C ws/scripts pi3_start.sh pi3_stop.sh`，
  归档根就是 `install/` 与两个脚本，解到 `~/pi3_ws/.staging` 后 `mv` 到位）
- **先暂存校验、再原子替换**：不要在设备上"先删旧 install 再解包"——解包一旦失败（磁盘满/包损坏）设备就没有 install 了，节点再也起不来
- **必须用 `{ ...; } >log 2>&1 &` 包住整组命令**：若只重定向后台命令自身（`cd x && cmd >log 2>&1 &`），
  后台子 shell 仍持有 ssh 的 stdout 管道，ssh 会一直挂到超时（实测 rc=124）
- 起节点后 `sleep 10` 再校验；失败时看 Pi3 上 `~/pi3_ws/pi3_run.log`
- 用 `pgrep -f 'pi3_[b]ringup'`（方括号写法）避免 ssh 自身命令行被匹配到

#### 方式 B：手工 scp（CI 不可用时）

```bash
# 编译产物在 Hermes 容器 /opt/data/pi3build_deploy/install (= 宿主 /home/pi/hermes-data/pi3build_deploy/install)
scp -r /home/pi/hermes-data/pi3build_deploy/install pi@192.168.3.64:~/pi3_ws/pi3_install
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

- **2026-10-13**: CI 补齐自动部署与发布 —— `.gitea/workflows/deploy-pi3.yml`(推送 main: colcon build → 打包 `install`+启动脚本 → scp 到 Pi3 → 停旧节点/替换 install/重启 → 校验进程)、`.gitea/workflows/release.yml`(打 tag `v*`: 建 Release + 上传 `jetauto-vX.X.X.tar.gz`); 原 `build.yml`(仅编译) 删除
- **2026-10-12 (v0.10.1)**: 目录扁平化后的文档与路径同步(`pi3/{src,scripts,doc}` → `src`/`scripts`/`doc`); 代码位置改为 `/workspace/HiWonder_JetAuto`(宿主 `/home/pi/workspace`), 编译命令改为在 `/ws` 里 build; `sllidar_ros2` 子模块路径修复为 `src/sllidar_ros2`
- **2026-08-04 (v0.10.0)**: 全向碰撞检测（前/左/右三扇区，旋转按转向侧 STOP 0.15m / SLOW 0.30m）；旋转堵转检测（IMU 角速度 <0.08rad/s 持续 1s → 停车+蜂鸣，参数 stall_angular_threshold/stall_detect_time/safety_side_angle）；app_cmd_vel angular 限幅 0.5→0.6
- **2026-08-01**: controller_manager float() 防御(修 int position 崩溃); 舵机脉冲硬限幅 312-688
- **2026-07-29 (v0.9.9)**: 舵机限幅 ±45°、LiDAR 防撞保护、pi3_stop.sh
