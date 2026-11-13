# 实测机器与匹配边界

本项目针对一台 **雷神猎刃 R16 / THUNDEROBOT R16**。硬件识别主要采集于 2026-11-05，功能状态更新至 2026-11-13。相同商品名的其他 SKU 不一定使用相同主板、面板或外设，使用前应核对下表。

## 主机与显示

| 项目 | 本机记录 |
| --- | --- |
| 主机 / 主板 | THUNDEROBOT R16 / NLYA |
| BIOS | AMI TP181；记录的发布日期为 2025-05-05 |
| CPU | Intel Core i9-13900HX，8P + 16E，24 核 32 线程 |
| 内存 | 48 GiB；Lexar LD5S24G56C46ST ×2，每条 24 GiB；DDR5-5600，记录的配置速率 5600 MT/s |
| Intel 核显 | Intel UHD Graphics，PCI `8086:A788` rev04，Windows 子系统字段 `SUBSYS_1570152D`；ACPI `\_SB.PC00.GFX0` |
| NVIDIA 独显 | GeForce RTX 5080 Laptop GPU，PCI `10DE:2C19` revA1，Windows 子系统字段 `SUBSYS_1564152D`；ACPI `\_SB.PC00.PEG1.PEGP` |
| 内屏 | BOE NE160QDM-NZL / BOE0D55，2560 × 1600 |
| 当前成功 macOS 显示模式 | 核显路线主要以 2560 × 1600、60 Hz 使用；高刷实验关闭 |
| 图形模式 | 本机可切换独显直连和核显 / 独显混合模式；两条成功路线使用各自配置，不能据此认定双 GPU 同时呈现已通过 |

Windows 曾在核显路径枚举和使用 240 Hz；这不是 macOS 冷启动、DSC 或面板全部模式的验收。本项目也不根据面板型号单独承诺 300 Hz。HDMI、USB-C 视频输出与每个物理接口的 GPU 归属尚未全部核实。

## 存储与外设

| 项目 | 本机型号或标识 |
| --- | --- |
| 内置 NVMe 1 | Samsung 970 EVO Plus 500GB，固件 2B2QEXM7，控制器 `144D:A808` |
| 内置 NVMe 2 | Crucial P3 Plus CT1000P3PSSD8 1TB，固件 P9CR413，控制器 `1344:5416` |
| macOS 实验介质 | HIKSEMI USB 外置 SSD；系统通过外置盘的 OpenCore 启动 |
| 有线网 | Realtek PCIe GbE，PCI `10EC:8168` rev15 |
| Wi-Fi | Realtek RTL8852BE，PCI `10EC:B852` |
| 蓝牙 | Realtek USB `13D3:3570`，内部 USB HS07 |
| 板载音频 | Realtek ALC256，codec `10EC:0256`；Intel 控制器 `8086:7A50` |
| NVIDIA 显示音频 | HDA 控制器 `10DE:22E9`，codec `10DE:00AB`；本项目未完整验收 HDMI / DP 音频 |
| 键盘 | ACPI `CBKB0001` / `PNP0303`，PS/2 资源路径 `PC00.PS2K` |
| 触摸板 | Synaptics `SYN1B8B` / `PNP0C50`，I2C-HID；`PC00.I2C0.TPD0`，I2C 地址 0x2C；控制器 `8086:7A4C` |
| USB 主控 | Intel XHCI `8086:7A60`，`PC00.XHCI` |
| 摄像头 | FHD Webcam，USB `0408:50D1`，内部 HS06 |
| 电池 / 接电对象 | ACPI `BAT0` / `ADP1`，真实 EC 为 `PC00.LPCB.EC0` |

后置 USB-C 对应当前映射的 HS02 / SS02。该接口具有给笔记本充电的能力，用户确认同一充电器与线缆在 Windows 可用；macOS 当前故障见 [STATUS.md](STATUS.md)。标称 140 W、USB-C 接头或固件内的 Thunderbolt 模板，都不能单独证明已具备可用的 Thunderbolt / USB4 PCIe 通道。

## 已使用的软件环境

| 层次 | 记录 |
| --- | --- |
| macOS | Tahoe 26.7.2，build 25G332，Darwin 25.6.0，x86_64 |
| OpenCore | 1.0.9 |
| SMBIOS 产品型号 | MacBookPro16,2；序列号、MLB、ROM 和 SystemUUID 必须由使用者自行生成 |
| 核显路线 | 带 R16 补充的 WhateverXe 0.8.0 自编译版本；另依赖系统侧兼容 kext / 图形用户态组件，单独复制 EFI 不构成完整安装 |
| 独显直连历史路线 | NullMoth NVIDIA 2.7.2；其内核扩展、Metal 用户态组件与 GSP 固件安装在 macOS 系统侧，不能以 EFI 中未见 NVIDIA kext 推定未安装 |
| 无线基本功能通过版本 | AirportRTW 2.3.1，使用系统原生 IO80211Family；蓝牙保留 RealtekBluetoothFirmware 1.0.2 和 BlueToolFixup |

这里的社区图形支持不代表 Apple 或 NVIDIA 官方支持这台机器。不要直接套用其他电脑的 ACPI 地址、GPIO、USB 映射或 EC 命令。公开副本不包含本机序列号、MAC 地址、系统卷 UUID、原始 IORegistry / NVRAM 或私人机器路径。
