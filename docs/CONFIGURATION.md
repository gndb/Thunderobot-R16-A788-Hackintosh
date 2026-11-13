# 成功基线的配置解释

本页解释当前公开配置的主要选择；精确值以 `EFI/OC/config.plist` 为准。

| 层次 | 当前选择与目的 |
| --- | --- |
| 图形路线 | WhateverXe 开启，WhateverGreen 关闭。成功基线含 `-nvoff`，暂停系统侧 NVIDIA 认领，单独观察 A788。 |
| NVIDIA 预留 | 原有 `nvfb=1 nvaccel=1 nvfbheads=4 gfxrst=4` 等仍在；在 `-nvoff` 存在时，不应据这些参数认定独显正在工作。 |
| R16 加速器 / 输出 | `-wex-r16-panel-txn -wex-r16-panel-r5 -wex-r16-accel-r6`，配合严格设备与目标校验，补充本机输出流程和持久诊断。 |
| 首次显示接管 | `-wex-r16-handoff` 提供有界显示恢复尝试；出现过桌面，仍不能保证每次冷启动成功。 |
| 媒体兼容 | `-wex-r16-va-software` 是软件路径规避，不代表硬解、硬编和媒体编译全部通过。 |
| 亮度 | PNLF SSDT、BrightnessKeys 和 `-wex-r16-backlight64`。后者针对严格签名窗口内的 PWM 算术溢出，不改整套电源与唤醒流程。 |
| 暂停的试验 | 不含 `-wex-r16-resume-r10`、`-wex-r16-dim-r11`；两个 R16 240 Hz 参数与相应高刷二进制代码均不在成功基线中。 |
| 音频 | ALC256，`alcid=21`，AppleALC/SimpleHDA 与本机布局有关；不能保证其他 codec 或不同 OEM 电路可复用。 |
| CPU / SMC | CpuTopologyRebuild、SSDT-PLUG-ALT、VirtualSMC 与相应插件；不要把拓扑可见解释为调度或功耗已最优。 |
| 输入 | VoodooPS2 内键盘，VoodooI2C/HID 触摸板；依赖本机 ACPI/GPIO/XOSI 路径。 |
| 无线 | AirportRTW 2.3.1 走原生 IO80211Family；公开配置移除未启用的旧 Apple 网络 donor 加载条目。 |
| USB | USBToolBox + UTBMap，本机 12 个逻辑端口；SSDT-USB-Reset、USBX 保留。后置 Type-C 的 HS02/SS02 已列入，但数据/PD 故障仍未修好。 |
| USB 电源改名 | 先前作用于 xh_rplsb 的 GPLD/GUPC 改名补丁不在当前配置。它改变父控制器电源表加载，不是已定位的单端口 PD 修复。 |
| 启动参数更新 | NVRAM/Delete 已包含 `boot-args`，让配置变更在下次经本 OpenCore 启动时更新。 |
| 安全与调试 | 原基线的详细日志、调试和 AMFI 相关实验设置保留，不能当成适合所有日用机器的安全配置模板。 |

## 公开副本相对原始成功配置的差异

1. 清空 Generic 的序列号、MLB、SystemUUID，ROM 置六个零字节。
2. 去掉 `bluetoothInternalControllerInfo` 缓存身份。
3. 从 Kernel/Add 移除原来已禁用的加载条目；所有已启用条目的参数、顺序和配置保持。
4. 不复制历史 config、旧驱动、原始运行日志与系统 donor 材料。

脱敏后 config 的哈希与私人原件不同。WEX 和收录的 OpenCore/ACPI/UTBMap 二进制保留原字节。公开副本尚未单独进行硬件启动；原始成功会话、公开文件检查和后来双 GPU 试验分别记录在 metadata 中。
