# R16 状态报告：2026-11-14

本报告记录 THUNDEROBOT R16 / i9-13900HX / Intel A788 / RTX 5080 Laptop 的当前实验适配状态。它是状态更新，不代表仓库旧发布包已自动升级，也不是全功能稳定性承诺。

## 已取得的结果

|项目|最新可核对结果|边界|
|---|---|---|
|Intel图形栈|WEX0.8.2，保留R16定制；Compat0.8.1、Graphics ABI1、Graphics0.4.4|15:49启动已加载|
|内屏与亮度|2560×1600、60Hz，用户确认桌面和全范围连续亮度|睡眠、高刷及重复冷启动可靠性未完成|
|Intel基础Metal|1024元素计算及回读0错|不是视频、压力或全部图形应用验收|
|NVIDIA|四个GPU模块3.0实际加载，仍headless|最近七项双卡基础回归属于此前13:10会话；本次082窗口未重跑|
|CPU策略|CPUFriend1.3.0已加载|加载不证明性能、EPP寄存器或续航收益|
|输入、音频、无线、USB-A|历史用户功能确认及基础检查已通过|不因本轮未重复而改判失败，也不扩大为长期/恢复验收|

原有R16背光64位和软件媒体回退仍生效。图形栈应配套更新；参考[WEX0.8.2](https://github.com/b00t0x/WhateverXe/releases/tag/0.8.2)与[Graphics0.4.4](https://github.com/b00t0x/WhateverXe-Graphics/releases/tag/v0.4.4)。

## Type-C检查结果

Windows既有原生拓扑支持后置数据口位于PCH7A60，HS02/SS02及connector9映射有真实设备依据。已测试保留RHUB ACPI子树：停用USB-Reset表并使用USBToolBox的-utbacpioff；12口映射仍应用，RHUB和目标ACPI端口均已出现。

但15:20对照记录中，用户接着USB数据设备仍无反应，目标端口没有连接事件。因此该实验没有解决Type-C，不能标为完成。140W输入充电、USB数据、DP视频与雷电能力是不同项目；没有VBUS或PD合同测量，不以USBX电流或软件功率数字代替。[USBToolBox开关说明](https://github.com/USBToolBox/kext#configuration)

本轮Windows标准CIM进一步确认PCH7A60及HIKSEMI等USB设备仍存在，所取记录没有设备问题码。普通token原生枚举未取得完整物理拓扑，位置属性查询又超时，因此没有据此断言当前后置口是否插着设备或已损坏。此结果不能替代文件系统完整性、USB吞吐或PD测量。

## 仍保留的问题

- 冷启动显示交接可靠性、多苹果/短闪，以及熄屏/睡眠后黑屏；当前一次成功不关闭历史故障。
- WebKit/编译服务的图形插件可执行映射拒绝；小规模Metal通过不代表全部沙盒应用正常。
- BetterDisplay应用UD2崩溃。最新故障位于应用自身，缺少足够证据归责显卡或CPU指令集。
- 历史WindowServer资源占用/同步等待、私有媒体模型编译、Safari部分视频绿闪和完整硬件视频编解码。
- OEM ACPI表冲突、电池/EC/风扇遥测、后置Type-C/PD，以及外屏逐接口能力。
- 240/300Hz、长期负载、完整内存/存储稳定性、全部厂商功能尚未通过。

## 资料完整性与发布范围

本轮整理发现部分协作报告与机器索引内容异常。原因未定，原材料已进入保全/恢复核对；未把异常材料当作新测试成功，也未把它直接诊断为硬件损坏。此报告采用仍有效的原始验收记录与可追溯历史状态重建。

公开内容只保留硬件型号、版本、测试范围和问题摘要，不含序列号、MAC、启动或系统卷身份、私人路径与原始完整日志。仓库已有的历史成功配置应按其原版本说明使用；本报告不能替代新版本的完整依赖、脱敏与实机验收。

## 全部问题追踪

| 编号 | 问题 | 当前状态 |
| --- | --- | --- |
| SHARE-INTEGRITY | share报告及机器索引内容异常 | 本轮新确认，最高优先处理 |
| USB-C | 后置Type-C数据设备不识别 | RHUB保留实验生效，但15:20仍失败 |
| USB-PD | Type-C给电脑140W输入充电 | 历史未识别接电，仍未解决 |
| BOOT-DISPLAY | 冷启动黑屏、多苹果/短闪 | 最新一次082启动成功，可靠性未关闭 |
| GRAPHICS-SANDBOX-LOAD | 沙盒应用映射图形插件被拒 | 最新082启动仍存在 |
| BETTERDISPLAY | BetterDisplay应用崩溃 | 最新082启动再次确认 |
| COMPOSITOR | WindowServer CPU/同步等待偏高 | 历史仍待定位，新窗口不足比较 |
| RESUME | 熄屏/睡眠后黑屏 | 历史故障保留，测试暂停 |
| REFRESH | 240/300Hz与DSC/HDR/VRR | 关闭，未完成可靠验收 |
| MEDIA-COMPILE | 系统私有媒体模型编译 | 历史待同场景复验 |
| VIDEO-HW | 完整硬件视频编解码 | 尚未通过，软件规避保留 |
| SAFARI-GREEN | Safari部分视频绿闪 | 历史未关闭，现按用户要求暂停 |
| ACPI-USBPOWER | xh_rplsb/GPLD/GUPC冲突 | 历史加载失败未解决 |
| ACPI-THERMAL | Ther_Rvp/ETMD表冲突 | 历史确认，当前因果未定 |
| ACPI-ECPCI | 电池EC及PCI初始化错误 | 历史异常，功能部分正常 |
| FAN-RPM | 风扇RPM遥测 | 接口未发布，不代表风扇停转 |
| MIC-TCC | 应用级麦克风授权 | 历史未复验 |
| CPU-POLICY | CPUFriend/EPP与性能收益 | 当前CPUFriend1.3.0已加载，收益未定 |
| TGP-PERFORMANCE | NVIDIA功耗开关与性能 | 开关存在，性能收益不确定 |
| EXTERNAL-DISPLAY | HDMI/USB-C视频/雷电USB4 | 逐接口未完整验收 |
| STORAGE-LONGTERM | 存储APST/TRIM及长期恢复 | 基础可见/健康通过，长期未验 |
| MEMORY-LONGTERM | 完整48GiB与长期内存稳定 | 局部短测通过，整体未验 |
| VENDOR-FEATURES | 厂商风扇/性能/RGB/充电上限 | macOS未完整适配 |

本次为报告更新。仓库EFI及2026-11-13历史配置包仍保留其原版本，未被替换为已安装新图形栈的完整启动镜像。
