# 雷神 R16 黑苹果适配

i9-13900HX · Intel UHD A788 · RTX 5080 Laptop · BOE NE160QDM-NZL

保存这台 R16 的 EFI、R16 版 WhateverXe 源码、工具和问题记录。当前内屏由 Intel 驱动，NVIDIA 作为 headless 设备；高刷关闭。

**公开 EFI 是脱敏配置和部分载荷，需补齐依赖及自己的 SMBIOS。Intel／NVIDIA 系统侧组件另行安装。**

## 配置

| 入口 | 内容 | 状态 |
|---|---|---|
| [EFI/](EFI/) | 当前部署：WEX 0.8.2-R16，UTBMap 1.0.3，AirportRTW 2.3.3 依赖 | USB 修订后的完整运行验收待补 |
| [11月14日成功备份](profiles/usable-20261114/) | 对应15:49会话的配置与依赖 | 桌面、60 Hz、亮度和小型 Intel 计算有成功记录 |

后置 Type-C 为 **HS04／SS02**，connector 9，companion 字段 **17／3**；默认 EFI 已同步。USB-C 供电、显示恢复和媒体兼容仍有问题，见[当前状态](docs/STATUS.md)。

## 导航

- [使用步骤](docs/INSTALL.md) · [硬件清单](docs/HARDWARE.md)
- [当前问题](docs/STATUS.md) · [版本与验证记录](docs/HISTORY.md)
- [源码、构建与贡献](docs/DEVELOPMENT.md) · [来源与许可](docs/THIRD_PARTY.md)
- [发行包](https://github.com/gndb/Thunderobot-R16-A788-Hackintosh/releases)

## 目录

| 目录 | 用途 |
|---|---|
| `EFI/` | 当前公开配置与允许分发的载荷 |
| `profiles/usable-20261114/` | 已出图会话的恢复参考 |
| `src/`、`patches/` | 当前源码、补丁和诊断源文件 |
| `tools/`、`contributions/` | 检查、采集和独立贡献 |
| `docs/`、`metadata/` | 人读说明、版本与文件指纹 |

旧实验档和重复快照已从主目录收起，仍可从[历史索引](docs/HISTORY.md)恢复。
