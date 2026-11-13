# 使用步骤

这是从已成功会话整理的配置与本机修改，属于实验适配。先阅读 [硬件表](HARDWARE.md)、[功能状态](STATUS.md) 和 [依赖表](DEPENDENCIES.md)。

## 1. 准备完整的测试副本

保留自己的完整 EFI。本仓库只提供部分载荷，应在一个新的离线副本里合并文件，不要在尚未补齐依赖时整体替换活动 EFI。

- OpenCore 核心、10 个活动 SSDT、UTBMap 和自编译 WEX 在包内。
- 从依赖表的原始项目取得其余 kext、HfsPlus/apfs_aligned、NullMothSafe 和 OpenCanopy Resources。
- 以 `metadata/dependencies.json` 的版本与文件 SHA-256 核对。使用不同版本需重新测试。
- 不恢复已停用的 IOSkywalk/IO80211Legacy donor、WhateverGreen、旧 `WhateverXe.before-*` 或历史 config 副本。

## 2. 填入自己的机器标识

`PlatformInfo → Generic` 的 SystemSerialNumber、MLB、SystemUUID 已留空，ROM 为六个零字节；必须生成并填入自己的值。参考 [GenSMBIOS](https://github.com/corpnewt/GenSMBIOS) 和 [OpenCore 文档](https://github.com/acidanthera/OpenCorePkg/tree/master/Docs)。不要复制别人的真实标识。

成功会话模拟产品型号为 MacBookPro16,2。公开配置还去除了蓝牙控制器缓存身份。

## 3. 核对系统侧图形依赖

本机使用带补充的 WhateverXe 0.8.0，以及另行安装到 macOS 的 Graphics/Compat 配套。对应依赖不在 EFI 内，也不由本仓库的公开包安装。

- [WhateverXe-Graphics](https://github.com/b00t0x/WhateverXe-Graphics) 是图形用户态安装项目；本机历史安装回执为 0.4.0。
- 本机系统侧 AppleIntelTGLCompat 有实验修改。源码快照内同名目标不自动等同于本机正在使用的成功系统侧二进制，不能盲目替换。
- 本仓库不分发 Apple donor 内核驱动或系统框架，也没有把本机系统目录做成安装镜像。

因此本仓库首先用于保存和阅读本机成功配置；新装系统仍需自行完成这些图形依赖，不能声称只复制 EFI 即复现完整加速。

## 4. 保持图形路线清楚

公开基线启用 WEX、关闭 WEG，保留 `-nvoff` 暂停系统侧 NVIDIA 驱动。高刷和后来失败/待验的唤醒试验均关闭。使用前确认固件模式下内屏由核显路径输出。

NVIDIA 历史成功来自独显直连的另一套配置与系统侧 NullMoth 2.7.2。后来解除 `-nvoff` 的双 GPU 共存试验尚未验收；不要把两条独立成功相加成混合输出已成功。`nmhybrid` / `NMIntelFB` 是另一个输出方案，不在本次配置内。

## 5. 检查与实际启动

在仓库根目录运行 `python3 tools/verify_package.py`，再使用与 OpenCore 构建匹配的 ocvalidate 检查填好标识后的完整配置。公开包已通过一次 OpenCore 1.0.9 ocvalidate 检查，但填入标识、补齐依赖后的副本应由使用者自行核对。

首次测试保留外部恢复入口，正常选择 macOS。分别记录实际桌面、两块 GPU、Metal、显示归属和睡眠恢复结果；OpenCore 停在 EXITBS 不足以定位后续内核故障。
