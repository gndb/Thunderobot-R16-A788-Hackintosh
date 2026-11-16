# 依赖与精确版本

本表描述11月16日默认根EFI及latest-20261116；历史profile按各自日期的依赖和元数据使用，11月14日成功档仍使用其原依赖。公开包只提供部分载荷，需补齐所有启用条目。精确文件大小、SHA和公开包含范围见[默认依赖清单](../metadata/dependencies.json)。

| 组件 | 本机版本 | 本包包含 | 来源 |
| --- | --- | --- | --- |
| AMFIPass.kext | 1.4.1 | 需自备 | [项目/发行](https://github.com/dortania/OpenCore-Legacy-Patcher/tree/main/payloads/Kexts/Acidanthera) |
| AirportRTW.kext | 2.3.3 | 需自备 | [项目/发行](https://github.com/souissiak1-maker/AirportRTW/releases/tag/V2.3.3) |
| AppleALC.kext | 1.9.8 | 需自备 | [项目/发行](https://github.com/acidanthera/AppleALC) |
| BlueToolFixup.kext | 2.7.3 | 需自备 | [项目/发行](https://github.com/acidanthera/BrcmPatchRAM) |
| BrightnessKeys.kext | 1.0.4 | 需自备 | [项目/发行](https://github.com/acidanthera/BrightnessKeys) |
| CPUFriend.kext | 1.3.0 | 需自备 | [项目/说明](https://github.com/acidanthera/CPUFriend) |
| CPUFriendDataProvider.kext | 本机记录1.0.1 | 不分发原数据块，须自行生成 | [CPU政策](CPU_POLICY.md) |
| CpuTopologyRebuild.kext | 2.0.2 | 需自备 | [项目/发行](https://github.com/b00t0x/CpuTopologyRebuild) |
| ECEnabler.kext | 1.0.6 | 需自备 | [项目/发行](https://github.com/averycblack/ECEnabler) |
| Lilu.kext | 1.7.3 | 需自备 | [项目/发行](https://github.com/acidanthera/Lilu) |
| NVMeFix.kext | 1.1.4 | 需自备 | [项目/发行](https://github.com/acidanthera/NVMeFix) |
| RealtekBluetoothFirmware.kext | 1.0.2 | 需自备 | [项目/发行](https://github.com/thegwchr/RealtekBluetoothFirmware) |
| RealtekRTL8111.kext | 3.0.4 | 需自备 | [项目/发行](https://github.com/Mieze/RTL8111_driver_for_OS_X) |
| RestrictEvents.kext | 1.1.7 | 需自备 | [项目/发行](https://github.com/acidanthera/RestrictEvents) |
| SMCBatteryManager.kext | 1.3.9 | 需自备 | [项目/发行](https://github.com/acidanthera/VirtualSMC) |
| SMCLightSensor.kext | 1.3.9 | 需自备 | [项目/发行](https://github.com/acidanthera/VirtualSMC) |
| SMCProcessor.kext | 1.3.9 | 需自备 | [项目/发行](https://github.com/acidanthera/VirtualSMC) |
| SMCSuperIO.kext | 1.3.9 | 需自备 | [项目/发行](https://github.com/acidanthera/VirtualSMC) |
| SimpleHDA.kext | 1.0.1 | 需自备 | [项目/发行](https://github.com/laobamac/SimpleHDA) |
| USBToolBox.kext | 1.2.0 | 需自备 | [项目/发行](https://github.com/USBToolBox/kext) |
| UTBMap.kext | 1.0.3 | 是 | 本机10端口映射，后置HS04/SS02 |
| VirtualSMC.kext | 1.3.9 | 需自备 | [项目/发行](https://github.com/acidanthera/VirtualSMC) |
| VoodooI2C.kext | 2.9.1 | 需自备 | [项目/发行](https://github.com/VoodooI2C/VoodooI2C) |
| VoodooI2CHID.kext | 1 | 需自备 | [项目/发行](https://github.com/VoodooI2C/VoodooI2C) |
| VoodooPS2Controller.kext | 2.3.7 | 需自备 | [项目/发行](https://github.com/acidanthera/VoodooPS2) |
| WhateverXe.kext | 0.8.2-R16 | 是 | [项目/发行](https://github.com/b00t0x/WhateverXe) |
| XHCI-unsupported.kext | 0.9.2 | 需自备 | [项目/发行](https://github.com/daliansky/OS-X-USB-Inject-All) |


## 系统侧图形栈

| 组件 | 15:49会话记录 | 分发处理 |
|---|---|---|
| WhateverXe.kext | 0.8.2-R16 | 本仓库提供对应自编载荷与源码补丁 |
| Graphics | 安装记录0.4.4、ABI1 | 按[原项目](https://github.com/b00t0x/WhateverXe-Graphics/releases/tag/v0.4.4)取得，系统侧另装 |
| AppleIntelTGLCompat | 0.8.1 | 系统侧配套，不等于本次WEX源码构建的任意同名产物 |
| NullMoth NVIDIA | 3.0，四模块加载，headless | 按[官方v3.0](https://github.com/nullmoth/nvidia-macos-driver/releases/tag/v3.0)取得系统侧载荷 |

HfsPlus、apfs_aligned、NullMothSafe、OpenCanopy资源及其余第三方依赖按清单补齐。Apple donor、系统框架、固件合集和SimpleHDA涉及的系统侧材料不随本仓库再分发。

CPUFriend启用范围记录为Darwin25.0.0–25.99.99；全局EPP64只是本机政策差异，未证明性能收益。DataProvider中原始电源XML不公开，生成自己的Provider后再组装测试配置。

历史11月13日05:27七项档使用旧WEX0.8.0和NVIDIA2.7.2、有线2.4.2；旧根快照的有线3.0.4仅有引导注入范围。它们不能与本表的新版会话交叉拼接。
