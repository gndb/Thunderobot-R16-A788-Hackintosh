# 雷神 R16 · Intel A788 黑苹果适配记录

> **2026-11-14 状态更新**：[最新报告与全部问题](docs/CURRENT_REPORT_20261114.md)。本机现已运行WEX0.8.2/Graphics0.4.4/Compat0.8.1与NVIDIA3.0；Type-C仍未解决。此提交只更新报告，仓库EFI与旧发布包仍是2026-11-13基线，请按各包版本说明使用。


**i9-13900HX / Intel UHD A788 / RTX 5080 Laptop / BOE NE160QDM-NZL**

本仓库记录一台雷神猎刃 R16 的真实配置、成功基线和已知问题，并提供脱敏配置、ACPI、USB 映射及自编译 WhateverXe 的对应源码。更新日期：**2026-11-13**。

2026-11-13配置包为 **核显内屏 2560×1600、60 Hz ＋ RTX 5080 headless 双GPU共存配置**。两块GPU分别完成计算、清屏、着色器绘图及读回，同一进程双队列也通过。首次显示接管、熄屏唤醒、USB-C 与媒体兼容仍有问题，不能当成全功能稳定方案。

## 机器参数

| 项目 | 实测机器 |
| --- | --- |
| 整机 / 主板 / BIOS | THUNDEROBOT R16 / NLYA / AMI TP181 |
| CPU | Intel Core i9-13900HX，8P+16E，24 核 32 线程 |
| 内存 | 48 GiB，Lexar DDR5-5600 24 GiB ×2 |
| 核显 | Intel UHD Graphics，`8086:A788` rev04 |
| 独显 | NVIDIA GeForce RTX 5080 Laptop，`10DE:2C19` |
| 内屏 | BOE NE160QDM-NZL / BOE0D55，2560×1600 |
| NVMe | Samsung 970 EVO Plus 500GB；Crucial P3 Plus 1TB |
| 无线 / 蓝牙 | Realtek RTL8852BE / USB `13D3:3570` |
| 音频 / 触摸板 | Realtek ALC256 / Synaptics SYN1B8B I2C-HID |
| 系统环境 | macOS Tahoe 26.7.2（25G332），Darwin 25.6.0；OpenCore 1.0.9 随包构建 |

具体设备 ID、固件、ACPI 路径和接口边界见 [完整硬件表](docs/HARDWARE.md)。同名 R16 的其他配置不一定相同。

## 已成功与未解决

| 项目 | 状态 |
| --- | --- |
| 系统安装、桌面、A788 基础 Metal | 已有实际结果；未完成长期稳定性验收 |
| 亮度滑条 / 亮度键 | 基本可用；按键为阶梯调光 |
| 键盘、触摸板、左右喇叭、内麦 | 基本功能已有成功记录 |
| Wi-Fi / 蓝牙 | AirportRTW 2.3.1 组合，用户确认基本正常 |
| NVIDIA 独显直连 | 历史独立配置以 NullMoth 2.7.2 完成过 Metal 测试 |
| 核显与 NVIDIA 同时工作 | **7个基础作业案例通过**；核显负责内屏，独显headless，非跨GPU画面转交 |
| 有线网卡 | 精确实测档为2.4.2；现用快照3.0.4已引导注入，尚缺新版链路/流量验收 |
| 冷启动黑屏、熄屏唤不醒、整机睡眠 | 仍待修复或完整验收 |
| 后置 USB-C 数据 / 给电脑 PD 充电 | macOS 下仍有故障；Windows 同组合可用 |
| 240 / 300 Hz | 当前关闭；曾会话内出图不等于冷启动可靠 |
| 视频媒体编译 / 完整硬解硬编 | 未全部修复，已有规避路径 |

完整结论、证据层次和限制见 [功能状态](docs/STATUS.md)。

## 配置档案

下表是2026-11-13归档配置；不代表11月14日新图形栈已作为完整EFI分发。

| 档案 | 内容与验证范围 |
| --- | --- |
| [当前快照：EFI/](EFI/OC/config.plist) | 现用双GPU图形栈；去掉-v、有线升级3.0.4，新有线仅确认引导注入 |
| [精确实测双GPU](profiles/dual-gpu-verified-0527/EFI/OC/config.plist) | 05:27成功会话配置，保留-v、有线2.4.2；与7项作业结果对应 |
| [原核显独立基线](profiles/igpu-only-20261113/EFI/OC/config.plist) | 含-nvoff，作为早前核显路线对照 |

两个双GPU配置的显卡驱动、ACPI、USB和亮度设置相同。所有配置都必须填自己的SMBIOS、补齐依赖；目录中的配置档案共用根EFI载荷，不能把仅有config的小目录当完整EFI。详见 [双GPU实测与档案](docs/DUAL_GPU.md)。

## 下载内容

- `EFI/`：现用双GPU配置快照、10个活动ACPI、UTBMap、自编WEX和OpenCore核心文件。
- `profiles/`：精确双GPU实测档与原核显独立基线。
- `src/metal-smoke/`：本次实测对应的三个Metal小测试源码；脱敏结果在metadata。
- `src/WhateverXe/`：与本机 WEX 二进制构建清单匹配的源码快照、许可和源码哈希。
- `metadata/`：基线身份、组件版本、文件 SHA-256 及依赖清单。
- `docs/`：安装、配置解释、完整机器参数、状态、源码来源与许可边界。

**下载包尚需补齐第三方依赖和自己的 SMBIOS，不能直接整包替换启动盘。** 为避免夹带个人身份、历史恢复文件和未核实再分发的系统材料，本包没有收录原始日志、旧配置、Apple donor 驱动及全部第三方二进制。所需版本和精确文件哈希均已记录，见 [依赖表](docs/DEPENDENCIES.md) 和 [使用步骤](docs/INSTALL.md)。

## 使用与核对

1. 对照硬件表，保留现有完整 EFI 和可恢复入口。
2. 按依赖表准备完整副本，合并本仓库的配置和本机补充；生成自己的序列号、MLB、ROM 与 SystemUUID。
3. 核显路线还需要 macOS 系统侧 Graphics / Compat 配套；按安装说明核对，不能只靠 EFI。
4. 当前双GPU配置已移除 `-nvoff`，保留WEX和系统侧NullMoth **2.7.2**，高刷关闭；未升级2.9、未开启 `nmhybrid/NMIntelFB`。

离线检查公开包：

```sh
python3 tools/verify_package.py
```

这项检查验证脱敏、哈希和配置边界，不代表在另一台机器上启动或硬件验证通过。

## 修改与来源

本机 WEX 仍显示 0.8.0，实际含 R16 的设备门禁、输出与加速器诊断、首次接管重试、媒体规避及 64 位背光算术修正。详见 [源码与构建来源](docs/SOURCE.md) 和 [配置说明](docs/CONFIGURATION.md)。

感谢 [WhateverXe](https://github.com/b00t0x/WhateverXe)、[rodgod-rr 的 HX 研究](https://github.com/rodgod-rr/WhateverXe)、[NullMoth](https://github.com/nullmoth/nvidia-macos-driver)、[OpenCore](https://github.com/acidanthera/OpenCorePkg) 及各组件作者。本仓库不代表 Apple、NVIDIA 或整机厂商的官方支持，不承诺同设备 ID 的其他电脑可直接复用。

自有说明与配置整理适用 [MIT 许可](LICENSE)；WEX、OpenCore 和其他来源内容保留各自许可，见 [来源与再分发说明](docs/THIRD_PARTY.md)。
