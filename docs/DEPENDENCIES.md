# 依赖与精确版本

这是公开的成功配置、ACPI、USB映射和自编译WhateverXe源码/二进制。其他系统及第三方驱动不在包内；需按表补齐。版本不同应另测，不把下载到的新版本当本机已验。

| 组件 | 本机版本 | 本包包含 | 来源 |
| --- | --- | --- | --- |
| AMFIPass.kext | 1.4.1 | 需自备 | [项目/发行](https://github.com/dortania/OpenCore-Legacy-Patcher/tree/main/payloads/Kexts/Acidanthera) |
| AirportRTW.kext | 2.3.1 | 需自备 | [项目/发行](https://github.com/souissiak1-maker/AirportRTW/releases/tag/V2.3.1) |
| AppleALC.kext | 1.9.8 | 需自备 | [项目/发行](https://github.com/acidanthera/AppleALC) |
| BlueToolFixup.kext | 2.7.3 | 需自备 | [项目/发行](https://github.com/acidanthera/BrcmPatchRAM) |
| BrightnessKeys.kext | 1.0.4 | 需自备 | [项目/发行](https://github.com/acidanthera/BrightnessKeys) |
| CpuTopologyRebuild.kext | 2.0.2 | 需自备 | [项目/发行](https://github.com/b00t0x/CpuTopologyRebuild) |
| ECEnabler.kext | 1.0.6 | 需自备 | [项目/发行](https://github.com/averycblack/ECEnabler) |
| Lilu.kext | 1.7.3 | 需自备 | [项目/发行](https://github.com/acidanthera/Lilu) |
| NVMeFix.kext | 1.1.4 | 需自备 | [项目/发行](https://github.com/acidanthera/NVMeFix) |
| RealtekBluetoothFirmware.kext | 1.0.2 | 需自备 | [项目/发行](https://github.com/thegwchr/RealtekBluetoothFirmware) |
| RealtekRTL8111.kext | 2.4.2 | 需自备 | [项目/发行](https://github.com/Mieze/RTL8111_driver_for_OS_X) |
| RestrictEvents.kext | 1.1.7 | 需自备 | [项目/发行](https://github.com/acidanthera/RestrictEvents) |
| SMCBatteryManager.kext | 1.3.9 | 需自备 | [项目/发行](https://github.com/acidanthera/VirtualSMC) |
| SMCLightSensor.kext | 1.3.9 | 需自备 | [项目/发行](https://github.com/acidanthera/VirtualSMC) |
| SMCProcessor.kext | 1.3.9 | 需自备 | [项目/发行](https://github.com/acidanthera/VirtualSMC) |
| SMCSuperIO.kext | 1.3.9 | 需自备 | [项目/发行](https://github.com/acidanthera/VirtualSMC) |
| SimpleHDA.kext | 1.0.1 | 需自备 | [项目/发行](https://github.com/laobamac/SimpleHDA) |
| USBToolBox.kext | 1.2.0 | 需自备 | [项目/发行](https://github.com/USBToolBox/kext) |
| UTBMap.kext | 1.1 | 是 | 本机映射 |
| VirtualSMC.kext | 1.3.9 | 需自备 | [项目/发行](https://github.com/acidanthera/VirtualSMC) |
| VoodooI2C.kext | 2.9.1 | 需自备 | [项目/发行](https://github.com/VoodooI2C/VoodooI2C) |
| VoodooI2CHID.kext | 1 | 需自备 | [项目/发行](https://github.com/VoodooI2C/VoodooI2C) |
| VoodooPS2Controller.kext | 2.3.7 | 需自备 | [项目/发行](https://github.com/acidanthera/VoodooPS2) |
| WhateverXe.kext | 0.8.0 | 是 | [项目/发行](https://github.com/b00t0x/WhateverXe) |
| XHCI-unsupported.kext | 0.9.2 | 需自备 | [项目/发行](https://github.com/daliansky/OS-X-USB-Inject-All) |

OpenCore 1.0.9 的 BOOTx64/OpenCore/OpenCanopy/OpenRuntime/ResetNvramEntry 已保留原二进制；许可见 licenses。

另外补齐 HfsPlus.efi、apfs_aligned.efi、NullMothSafe.efi 和 OpenCanopy Resources。精确文件大小与SHA-256见 [dependencies.json](../metadata/dependencies.json)。

SimpleHDA 包含系统侧Apple音频材料，本仓库不再分发；Apple网络donor kext未启用且不随包。

核显还依赖系统侧 Graphics/AppleIntelTGLCompat。历史报告的Graphics安装版本为0.4.0；当前Compat有本机修改，见SOURCE说明。单独复制EFI不能替代对应系统侧安装。

NVIDIA历史直连依赖NullMoth2.7.2的系统侧NVRM/NVAccel/NVRMFB/NVRMAGDC、Metal bundle与固件。本成功核显基线通过-nvoff暂停它们；新共存测试只是解除该禁用，尚无成功结果。
