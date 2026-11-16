# 适配硬件与版本

对象为一台雷神猎刃R16／THUNDEROBOT R16，主板NLYA、BIOS TP181。硬件识别主要来自11月5日记录，配置更新至11月16日；同名SKU可能使用不同主板、面板或外设。

本包按下表硬件制作。复用时先核对主板、BIOS、A788核显、面板、网络和USB接线；其他配置的适配状态为未验证。显示路线为Intel驱动内屏、NVIDIA headless。

## 硬件

| 项目 | 本机记录 |
|---|---|
| 主机／主板／BIOS | THUNDEROBOT R16／NLYA／AMI TP181（记录发布日期2025-05-05） |
| CPU | i9-13900HX，8P＋16E，24核32线程 |
| 内存 | 48 GiB，Lexar LD5S24G56C46ST 24 GiB ×2，配置速率5600 MT/s |
| Intel 核显 | UHD `8086:A788` rev04，`SUBSYS_1570152D`；`\_SB.PC00.GFX0` |
| NVIDIA 独显 | RTX 5080 Laptop `10DE:2C19` revA1，`SUBSYS_1564152D`；`\_SB.PC00.PEG1.PEGP` |
| 内屏 | BOE NE160QDM-NZL／BOE0D55，2560×1600；macOS成功记录为60 Hz |
| 内置存储 | Samsung 970 EVO Plus 500GB，2B2QEXM7，`144D:A808`；Crucial P3 Plus 1TB，P9CR413，`1344:5416` |
| macOS 介质 | HIKSEMI USB 外置 SSD，通过其 OpenCore 启动 |
| 有线／Wi-Fi | Realtek `10EC:8168` rev15／RTL8852BE `10EC:B852` |
| 蓝牙 | Realtek `13D3:3570`，内部 HS07 |
| 板载音频 | ALC256 `10EC:0256`，控制器 `8086:7A50` |
| NVIDIA 音频 | 控制器 `10DE:22E9`，codec `10DE:00AB`；HDMI／DP音频未完整验收 |
| 键盘 | `CBKB0001`／`PNP0303`，PS/2，`PC00.PS2K` |
| 触摸板 | Synaptics `SYN1B8B`／`PNP0C50`，I2C-HID，`PC00.I2C0.TPD0`，地址0x2C；控制器 `8086:7A4C` |
| USB 主控 | Intel XHCI `8086:7A60`，`PC00.XHCI` |
| 摄像头 | FHD Webcam `0408:50D1`，内部 HS06 |
| 电池／接电／EC | `BAT0`／`ADP1`／`PC00.LPCB.EC0` |

本机可切换独显直连与混合模式；本仓库当前路线为 Intel 内屏＋NVIDIA headless。Windows 曾使用240 Hz，macOS高刷保持关闭，面板型号本身不构成300 Hz承诺。外屏接口的GPU归属、自动MUX和跨GPU呈现仍待核实。

后置 Type-C 已由11月15日实插确认为 HS04／SS02，当前映射1.0.3的配对字段为17／3。标称140 W充电能力、Type-C接头或固件Thunderbolt模板，不等于已验证USB4／Thunderbolt通道；供电异常见[USB专题](issues/usb-typec.md)。

## 本机配套版本

| 层次 | 记录 |
|---|---|
| macOS | Tahoe **26.7.2**，build **25G332** |
| 内核／架构 | Darwin **25.6.0**／x86_64 |
| OpenCore／SMBIOS型号 | **1.0.9**／MacBookPro16,2 |
| EFI核显组件 | WhateverXe **0.8.2-R16**，本机定制补丁 |
| 系统侧Intel | Graphics **0.4.4**＋AppleIntelTGLCompat **0.8.1**，ABI **1** |
| 系统侧NVIDIA | **3.0**，headless配置 |
| USB映射 | UTBMap **1.0.3**，后置HS04／SS02，companion **17／3** |
| 无线驱动 | AirportRTW **2.3.3** |

11月14日成功会话使用WEX0.8.2／Graphics0.4.4／Compat0.8.1／NVIDIA3.0；当前USB／无线修订之后的完整运行验收待补。版本表用于复现本机记录的组合，不表示所有Tahoe26.x、所有R16或全部外设已经适配。文件级版本、来源与SHA256见[当前依赖清单](../metadata/dependencies.json)。

历史 WEX0.8.0／NV2.7.2 和较早无线版本的通过记录见[版本历史](HISTORY.md)。本机 ACPI、GPIO、USB 映射和 EC 地址不作为其他电脑的通用配置。
