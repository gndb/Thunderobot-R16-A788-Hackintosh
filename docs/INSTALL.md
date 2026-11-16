# 安装与首次测试

适配对象为R16／NLYA／TP181、Intel A788及本文记录的外设组合。先对照[硬件清单](HARDWARE.md)、[版本与状态](STATUS.md)及[包内容](PACKAGING.md)。公开扩展包已包含63个EFI文件，按完整清单补齐到179个，再填写自己的SMBIOS。

## 1. 下载同一档配置，补齐EFI文件

从[发行页](https://github.com/gndb/Thunderobot-R16-A788-Hackintosh/releases)选择对应包：

| 选择 | 配置与依赖 | 适用目的 |
|---|---|---|
| 当前版 | 根`EFI/`与[当前依赖](../metadata/dependencies.json) | 测试UTBMap1.0.3、HS04／SS02及AirportRTW2.3.3修订 |
| 11月14日成功回退版 | [独立目录](../profiles/usable-20261114/)内自己的配置、依赖与指纹 | 复现15:49可见桌面的已记录组合 |

按所选档依赖清单补齐所有启用的kext、UEFI驱动和资源。解压后的基本结构应包含`EFI/BOOT/BOOTx64.efi`和`EFI/OC/config.plist`；完整度以包内清单为准。

当前版可按[组装方法](PACKAGING.md#一条命令组装完整文件集)从原作者ZIP或已有匹配EFI准备完整目录。其指纹只适用于当前档，成功回退版使用自己的依赖，勿混用。

先在离线副本准备文件，保留原来的完整EFI及启动入口。不同档案的配置、WEX与系统侧组件按同一版本组合使用。

## 2. 填入自己的SMBIOS

所用型号为`MacBookPro16,2`。公开配置已清空`SystemSerialNumber`、`MLB`、`SystemUUID`，`ROM`为六个零字节，蓝牙私有NVRAM已移除。按[GenSMBIOS](https://github.com/corpnewt/GenSMBIOS)及[OpenCore文档](https://github.com/acidanthera/OpenCorePkg/tree/master/Docs)生成自己的标识，填入`PlatformInfo → Generic`。

这些字段和需要自行填写的原因见[打包与隐私说明](PACKAGING.md)。通用机型名、PCI设备ID和构建UUID用于说明兼容范围，保留在文档中。

### CPUFriendDataProvider

配置保留CPUFriend1.3.0及Provider1.0.1启用条目，限定Darwin25.0.0–25.99.99。若所选包未包含Provider，应按[CPUFriend说明](https://github.com/acidanthera/CPUFriend/blob/master/Instructions.md)准备适合自身系统模型的完整电源plist，再在隔离目录生成：

```sh
./ResourceConverter.sh --kext /path/to/own-modified-power.plist
```

本机配置意图为全局EPP64并保留原QoS，尚无独立性能／续航收益测量。若停用CPUFriend与Provider，记录为另一个测试配置。

## 3. 安装匹配的系统侧图形组件

| 位置 | 组件 | 本机配套 |
|---|---|---|
| EFI | WhateverXe | 0.8.2-R16 |
| macOS系统侧 | [WhateverXe-Graphics](https://github.com/b00t0x/WhateverXe-Graphics/releases/tag/v0.4.4) | Graphics0.4.4＋AppleIntelTGLCompat0.8.1，ABI1 |
| macOS系统侧 | [NullMoth NVIDIA](https://github.com/nullmoth/nvidia-macos-driver/releases/tag/v3.0) | 3.0，按原项目安装内核／Metal配套与GSP固件 |

本文记录系统为macOS Tahoe26.7.2（25G332）、Darwin25.6.0、x86_64。按各项目说明在macOS内安装并核对；其他系统版本另行验证。构建WEX得到的Compat也应核对版本与ABI。

当前配置采用Intel驱动内屏、NVIDIA headless，内屏60 Hz。系统侧组件不会因为复制EFI而自动安装。

## 4. 检查副本并从测试介质启动

在仓库运行公开包检查：

```sh
python3 tools/verify_package.py
```

准备好完整副本后，可再按所选档核对已知文件：

```sh
python3 tools/verify_package.py --profile current --efi /path/to/EFI
```

回退版将`--profile`改为`usable-20261114`。再用对应OpenCore构建的`ocvalidate`检查已经补齐依赖、填好标识的副本。

把准备好的`EFI/`文件夹放入独立测试介质的EFI分区，通过固件启动菜单选择它；保留原系统的启动入口。显示路径应与[本机配置](HARDWARE.md)一致。

第一次测试按顺序记录：可见60 Hz桌面、键盘／触摸板、音频与网络，再测试USB和图形作业。黑屏、熄屏恢复、Type-C供电及媒体问题按[状态页](STATUS.md)分项记录，注明所用配置与同一次启动。

Type-C可用[只读采集器](../tools/collect-usb-firmware/)读取HS04／SS02及固件属性。它不控制PD、EC或GPIO；枚举和文件校验通过均不等于供电或启动验收通过。
