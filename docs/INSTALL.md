# 安装与首次测试

适配对象为R16／NLYA／TP181、Intel A788及本文记录的外设组合。先对照[硬件](HARDWARE.md)、[系统与驱动版本](../README.md#二系统与驱动版本)和[当前状态](STATUS.md)。

## 1. 下载完整EFI

从[发行页](https://github.com/gndb/Thunderobot-R16-A788-Hackintosh/releases)下载当前完整包，或取得仓库根`EFI/`。当前文件集为179个文件，包含所用kext、UEFI驱动、资源和本机config；不包含旧config及旧USB映射备份。

解压后应为：

```text
EFI/
  BOOT/BOOTx64.efi
  OC/config.plist
  OC/ACPI/
  OC/Drivers/
  OC/Kexts/
  OC/Resources/
  OC/Tools/
```

当前包无需另行拼装EFI驱动。历史[11月14日成功回退参考](../profiles/usable-20261114/)使用自己的配置与依赖，不与当前包混装。

## 2. 核对SMBIOS与电源数据

当前config按机主授权保留原始身份，型号为`MacBookPro16,2`。其他使用者建议按[GenSMBIOS](https://github.com/corpnewt/GenSMBIOS)及[OpenCore文档](https://github.com/acidanthera/OpenCorePkg/tree/master/Docs)生成自己的`SystemSerialNumber`、`MLB`、`SystemUUID`和`ROM`，填入`PlatformInfo → Generic`。

包内已包含本机CPUFriend1.3.0及DataProvider1.0.1，限定Darwin25.0.0–25.99.99，记录全局EPP64策略。其他硬件若需调整，应按[CPUFriend说明](https://github.com/acidanthera/CPUFriend/blob/master/Instructions.md)从适合自身系统模型的电源plist生成新Provider：

```sh
./ResourceConverter.sh --kext /path/to/own-modified-power.plist
```

更换Provider或停用CPUFriend后，记为不同配置；当前策略没有独立性能／续航收益测量。

## 3. 安装系统侧图形组件

| 位置 | 组件 | 本机配套 |
|---|---|---|
| EFI内，已包含 | WhateverXe | 0.8.2-R16 |
| macOS系统侧，另装 | [WhateverXe-Graphics](https://github.com/b00t0x/WhateverXe-Graphics/releases/tag/v0.4.4) | Graphics0.4.4＋AppleIntelTGLCompat0.8.1，ABI1 |
| macOS系统侧，另装 | [NullMoth NVIDIA](https://github.com/nullmoth/nvidia-macos-driver/releases/tag/v3.0) | 3.0，按原项目安装内核／Metal配套与GSP固件 |

本机记录系统为macOS Tahoe26.7.2（25G332）、Darwin25.6.0、x86_64。当前Intel驱动内屏、NVIDIA headless，内屏60 Hz；高刷关闭。复制EFI不会自动安装系统侧组件，其他系统版本另行验证。

## 4. 检查并从测试介质启动

在仓库运行：

```sh
python3 tools/verify_package.py
python3 tools/verify_package.py --profile current --efi /path/to/EFI
```

再用对应OpenCore构建的`ocvalidate`检查准备使用的config。将`EFI/`放入独立测试介质的EFI分区，通过固件启动菜单选择它，保留原系统的启动入口。

第一次测试依次记录：可见60 Hz桌面、键盘／触摸板、音频与网络，再测USB和图形作业。黑屏、熄屏恢复、Type-C供电及媒体问题按[状态页](STATUS.md)分项记录，注明配置和同一次启动。

[USB只读采集器](../tools/collect-usb-firmware/)读取HS04／SS02及固件属性，不控制PD、EC或GPIO。文件检查、枚举结果和实际供电分别记录。
