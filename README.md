# 雷神 R16 黑苹果 EFI · macOS Tahoe

这是一台 **i9-13900HX＋Intel UHD A788＋RTX 5080 Laptop** 的实验性适配。当前采用 **Intel驱动内屏、NVIDIA headless** 的配置，内屏按60 Hz测试，高刷关闭。

## 一、适配硬件

| 项目 | 本机配置 |
|---|---|
| 机型／主板／BIOS | 雷神猎刃R16／NLYA／AMI TP181 |
| CPU／内存 | Intel Core i9-13900HX／48 GiB DDR5 |
| 核显／独显 | Intel UHD `8086:A788`／RTX 5080 Laptop `10DE:2C19` |
| 内屏 | BOE NE160QDM-NZL，2560×1600 |
| 无线／有线 | Realtek RTL8852BE／RTL8168 |
| 音频／输入 | ALC256／PS/2键盘＋Synaptics I2C触摸板 |
| 后置Type-C | HS04／SS02，connector 9，companion 17／3 |

同名R16可能有不同主板、面板和外设。使用前对照[完整硬件清单](docs/HARDWARE.md)，本机ACPI与USB映射按上述硬件制作。

## 二、系统与驱动版本

| 组件 | 本机配套版本 |
|---|---|
| macOS | Tahoe **26.7.2**，build **25G332** |
| 内核／架构 | Darwin **25.6.0**／x86_64 |
| OpenCore／SMBIOS型号 | **1.0.9**／MacBookPro16,2 |
| EFI核显组件 | **WhateverXe 0.8.2-R16**，包含本机补丁 |
| 系统侧Intel组件 | Graphics **0.4.4**＋AppleIntelTGLCompat **0.8.1**，ABI **1** |
| 系统侧NVIDIA组件 | **3.0**，headless配置 |
| USB映射／无线驱动 | UTBMap **1.0.3**／AirportRTW **2.3.3** |

以上是本机记录的组合；精确文件版本和指纹见[依赖清单](metadata/dependencies.json)。其他macOS版本及其他R16配置尚未逐一验证。

## 三、功能现状

| 功能 | 已有结果 | 当前限制 |
|---|---|---|
| 内屏显示／亮度 | 11月14日成功会话可见2560×1600／60 Hz桌面，亮度可调 | 冷启动接管及熄屏恢复仍有黑屏记录 |
| Intel GPU | 同次会话1024元素计算回读0错 | 完整媒体、应用和长期稳定性未验收 |
| NVIDIA GPU | 3.0四个内核模块有加载记录 | 新组合双GPU作业待复测；当前不驱动内屏 |
| 键盘／触摸板／音频／摄像头 | 有基本功能可用记录 | 全部功能与睡眠恢复待测 |
| 网络／USB-A | 有基本功能可用记录 | AirportRTW2.3.3和最新USB修订待完整复测 |
| 后置Type-C | Windows同口USB2／USB3.x正反插有枚举记录 | 给手机供电及给电脑充电异常仍在排查 |
| 外屏／高刷／完整视频加速 | 尚未完成验收 | 高刷关闭，外屏逐口与媒体兼容待测 |

最新EFI的USB／无线修订尚未完成同次启动验收。11月14日的成功结果单独保存在[成功回退版](profiles/usable-20261114/)，具体问题见[状态页](docs/STATUS.md)。

## 四、下载与使用

[下载发行包](https://github.com/gndb/Thunderobot-R16-A788-Hackintosh/releases) · [当前EFI](EFI/) · [成功回退版](profiles/usable-20261114/)

**发行页提供63文件驱动扩展包及配套源码；完整当前EFI需要179个文件。仍缺的组件、取得方式和一条命令组装方法见[打包说明](docs/PACKAGING.md)。每位使用者填写自己的SMBIOS。**

1. 核对硬件与版本，下载对应包；当前版可用[组装工具](tools/assemble_efi.py)按精确指纹补齐179文件，缺项会明确提示。
2. 为`MacBookPro16,2`生成自己的SMBIOS标识，填入所选配置。
3. 在macOS内单独安装表中匹配的Intel／NVIDIA系统侧组件。
4. 保留原EFI，用独立测试介质启动，先确认60 Hz桌面和基本功能，再按问题项测试。

完整步骤见[安装说明](docs/INSTALL.md)。EFI文件齐全与系统侧显卡组件安装是两个步骤；本项目目前仍有显示恢复和供电问题。

## 资料

[硬件](docs/HARDWARE.md) · [状态](docs/STATUS.md) · [版本历史](docs/HISTORY.md) · [源码与构建](docs/DEVELOPMENT.md) · [来源与许可](docs/THIRD_PARTY.md)

`EFI/`保存当前配置；`profiles/usable-20261114/`保存成功回退参考；`src/`和`patches/`保存当前源码及补丁，工具位于`tools/`。旧实验载荷可从[归档索引](docs/HISTORY.md)恢复。
