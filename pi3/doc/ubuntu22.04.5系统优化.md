
---

## 📋 树莓派3 Ubuntu 22.04.5 Server 精简优化清单（最终版）

### 1. 系统源切换（ARM架构专用）
- **操作**：将软件源切换为中科大 ARM 镜像源（`ubuntu-ports`）。
- **命令**：
  ```bash
  sudo sed -i 's@//.*/ubuntu/@//mirrors.ustc.edu.cn/ubuntu-ports/@g' /etc/apt/sources.list
  sudo apt update
  ```

### 2. 移除 Snap 及不必要的软件包
- **移除 snapd**（常驻后台，占用内存）：
  ```bash
  sudo systemctl stop snapd
  sudo apt purge snapd -y
  sudo rm -rf ~/snap /snap /var/snap /var/lib/snapd
  ```
- **移除蓝牙驱动与工具**（保留 WiFi）：
  ```bash
  sudo apt purge -y bluez pi-bluetooth
  ```
- **移除内核头文件与编译工具**（除非需要编译驱动）：
  ```bash
  sudo apt purge -y linux-headers-raspi linux-headers-$(uname -r) build-essential dkms
  ```
- **移除常见非必要服务**：
  ```bash
  sudo apt purge -y avahi-daemon cups whoopsie apport lxd multipath-tools modemmanager
  ```

### 3. 禁用无用内核模块（具体操作）
- **目的**：彻底阻止树莓派上不需要的多媒体、摄像头、图形、VCHI 等内核模块加载，消除 dmesg 中的错误并释放内存。
- **具体步骤**：
  1. 创建黑名单配置文件：
     ```bash
     sudo nano /etc/modprobe.d/raspberrypi-blacklist.conf
     ```
  2. 写入以下内容（每个模块一行，使用 `blacklist` 关键字）：
     ```
     # 禁用 VideoCore 共享内存驱动
     blacklist vc_sm_cma
     # 禁用 MMAL VCHI 驱动（多媒体抽象层）
     blacklist bcm2835_mmal_vchiq
     # 禁用 ISP 图像信号处理器驱动
     blacklist bcm2835_isp
     # 禁用 V4L2 视频采集驱动
     blacklist bcm2835_v4l2
     # 禁用硬件编解码器驱动
     blacklist bcm2835_codec
     # 禁用 Linux 媒体框架
     blacklist mc
     # 禁用 videodev 及相关的 videobuf2 模块
     blacklist videodev
     blacklist videobuf2_common
     blacklist videobuf2_vmalloc
     blacklist videobuf2_memops
     # 可选：禁用摄像头驱动
     blacklist bcm2835_unicam
     ```
  3. 更新 initramfs 使黑名单生效：
     ```bash
     sudo update-initramfs -u
     ```
  4. 重启后检查效果：
     ```bash
     dmesg | grep -E "vc_sm|bcm2835_mmal|bcm2835_isp|bcm2835_v4l2|bcm2835_codec"
     ```
     如果没有输出或仅有极少遗留信息，则说明禁用成功。

### 4. 禁用 AppArmor（内网不需要额外安全模块）
```bash
sudo systemctl disable --now apparmor
sudo apt purge apparmor -y
```

### 5. 精简 systemd 服务（禁用非必要后台服务）
- **注意**：保留 `getty@tty1.service`（物理控制台登录），不将其禁用。
- **一次性禁用以下服务**：
  ```bash
  sudo systemctl disable --now unattended-upgrades.service \
    serial-getty@ttyAMA0.service \
    rsyslog.service \
    irqbalance.service \
    networkd-dispatcher.service
  ```
- **可选禁用**（按需）：
  - `cron.service`（如果没有定时任务）
  - `systemd-timesyncd.service`（如果不介意时间不准）

### 6. 修复日志反复损坏问题（改用 volatile 存储）
- **操作**：将 systemd-journald 日志改为仅内存存储，避免频繁写入 SD 卡。
- **命令**：
  ```bash
  sudo systemctl stop systemd-journald
  sudo rm -rf /var/log/journal/*
  sudo sed -i 's/#Storage=auto/Storage=volatile/' /etc/systemd/journald.conf
  sudo systemctl start systemd-journald
  ```
- **效果**：重启后日志自动清空，不再出现 `user-1000.journal corrupted` 错误。

### 7. 优化 WiFi 电源管理（关闭省电模式，提高稳定性）
- **创建 systemd 服务** `/etc/systemd/system/wifi-powersave.service`：
  ```bash
  sudo nano /etc/systemd/system/wifi-powersave.service
  ```
  写入：
  ```ini
  [Unit]
  Description=Disable WiFi power save
  After=network.target

  [Service]
  Type=oneshot
  ExecStart=/usr/sbin/iw dev wlan0 set power_save off

  [Install]
  WantedBy=multi-user.target
  ```
- **启用服务**：
  ```bash
  sudo systemctl enable --now wifi-powersave.service
  ```

### 8. 释放 GPU 显存（仅命令行，不需要 GUI）
- 在 `/boot/firmware/config.txt` 末尾添加：
  ```bash
  echo "gpu_mem=16" | sudo tee -a /boot/firmware/config.txt
  ```

### 9. 禁用板载音频与蓝牙（保留 WiFi）
- 在 `/boot/firmware/config.txt` 末尾添加：
  ```bash
  sudo bash -c 'cat >> /boot/firmware/config.txt << EOF

  dtparam=audio=off
  dtoverlay=disable-bt
  EOF'
  ```

### 10. 清理残留与重启
```bash
sudo apt autoremove --purge -y
sudo apt clean
sudo reboot
```

---

## ✅ 优化后效果
- 内存占用降至 **~120MB 以下**。
- 启动速度加快，后台进程减少。
- SD 卡写入量降低（日志内存化），延长寿命。
- WiFi 稳定性提升（关闭电源管理）。
- dmesg 中不再出现多媒体驱动错误。
- 日志文件不再损坏报错。

## 📌 保留的核心功能
- SSH 远程登录
- WiFi 网络
- 物理控制台登录（getty@tty1.service）
- 基础系统管理（systemd, apt, 用户会话）
- 可选：时间同步、定时任务（按需保留）

---
