# 双 GPU 实测与配置档案

2026-11-13 05:27（UTC）启动的同一 macOS 会话中，Intel A788 驱动内屏，RTX 5080 Laptop 作为 headless Metal 设备工作。两块 GPU 的基础计算和绘图作业均取得正确读回结果。这次更新保存该会话的精确配置、稍后的现用快照及原核显独立配置。

## 三个配置的关系

| 档案 | config 位置 | 与实测会话的关系 |
| --- | --- | --- |
| 当前快照（默认） | [EFI/OC/config.plist](../EFI/OC/config.plist) | 同一显卡栈；去掉 `-v`，有线网卡更新至 3.0.4。新有线仅确认 OpenCore 注入，尚未验收链路与流量 |
| 精确双 GPU 实测档 | [profiles/dual-gpu-verified-0527/EFI/OC/config.plist](../profiles/dual-gpu-verified-0527/EFI/OC/config.plist) | 对应七项作业通过的会话；保留 `-v`，RealtekRTL8111 2.4.2 |
| 原核显独立档 | [profiles/igpu-only-20261113/EFI/OC/config.plist](../profiles/igpu-only-20261113/EFI/OC/config.plist) | 早前已出图的核显路线；含 `-nvoff`，停用 NVIDIA 认领 |

`profiles/` 内只保存 config、配置说明和依赖清单，共用根目录 `EFI/` 的其他载荷。切换档案时，以该档案的 `dependencies.json` 准备其余依赖，并填入自己的 SMBIOS。它们不是三个完整启动镜像。

两个双 GPU 档的 WEX、ACPI、USB、亮度设置相同，NVIDIA 系统侧均为 **2.7.2**。本次没有升级 2.9，没有启用 `nmhybrid` / NMIntelFB，没有恢复 240 Hz 参数。内屏为 2560×1600、60 Hz。

## 实测内容

| 作业 | Intel A788 | RTX 5080 Laptop |
| --- | --- | --- |
| 整数计算并读回 256 个元素 | 通过 | 通过 |
| 清屏并读回 16×16 纹理 | 通过 | 通过 |
| vertex + fragment 全屏三角形、16×16 像素读回 | 通过 | 通过 |
| 同一进程先向两张卡提交各自的计算队列，再等待结果 | 通过；末元素 1037 | 通过；末元素 2037 |

共七个作业案例，全部零读回差异、零超时。着色器使用两卡共同支持的 MSL 2.3。双队列使用各自资源与不同数据标记，没有跨 GPU 资源共享，也没有测量硬件执行时间是否重叠。

脱敏结果在 [dual-gpu-tests.json](../metadata/dual-gpu-tests.json)，对应的三个测试源码在 [src/metal-smoke/](../src/metal-smoke)。源码保留实际测试时的字节与 SHA-256。测试程序运行时会输出设备 registryID 和 servicePath；自行分享结果前应另行脱敏。本仓库未收录这些原始输出或启动 UUID。

## 验证范围

这次已经验证两块物理 GPU 在同一次启动中分别执行了基础 Metal 作业。Intel 仍负责内屏扫描输出；NVIDIA 的 headless 作业通过，不意味着它能把画面直接送到这个内屏。

尚未验证跨 GPU 帧转交、自动 MUX 切换、硬件执行重叠、两卡性能相加、全部 Metal 功能、完整硬件媒体编解码、外屏或长期负载。冷启动首次显示接管、熄屏与睡眠恢复仍列为未解决问题，见 [STATUS.md](STATUS.md)。

## 复用时的依赖

公开包只提供部分 EFI 载荷与本机补充源码。系统侧 Intel Graphics / Compat 以及 NVIDIA 2.7.2 配套不在包内，单独复制 EFI 不会安装它们。请按 [INSTALL.md](INSTALL.md) 与所选档案的依赖清单准备测试副本。

在仓库根目录运行 `python3 tools/verify_package.py` 可检查三个档案的脱敏、文件哈希、配置关系及测试记录。该脚本不进行硬件测试；公开的脱敏配置也未作为另一台机器的启动验收。
