# 使用步骤

本仓库提供实验配置和部分载荷。先核对[硬件](HARDWARE.md)与[状态](STATUS.md)，在保留完整 EFI 和恢复入口的离线副本中操作。

## 1. 选择配置并补齐依赖

- 当前配置：根 `EFI/`，按[当前依赖清单](../metadata/dependencies.json)补齐所有启用的 kext、UEFI 驱动和资源。
- 恢复参考：[11月14日成功备份](../profiles/usable-20261114/)，使用该目录自己的依赖清单。

两档的第三方文件版本、大小和 SHA256 均分别记录。不要将旧配置、历史 WEX 或系统侧版本混装。

## 2. 填入自己的 SMBIOS

公开配置使用 `MacBookPro16,2`，已清空 SystemSerialNumber、MLB、SystemUUID，ROM 为六个零字节，并移除蓝牙私有 NVRAM。使用者应生成自己的标识，参考 [GenSMBIOS](https://github.com/corpnewt/GenSMBIOS) 和 [OpenCore 文档](https://github.com/acidanthera/OpenCorePkg/tree/master/Docs)。

## 3. 生成 CPUFriendDataProvider

配置保留 CPUFriend 1.3.0 和本机 Provider 1.0.1 的启用条目，限定 Darwin 25.0.0–25.99.99；原 Provider 的完整电源 XML 和频率向量不分发。

按 [CPUFriend 官方说明](https://github.com/acidanthera/CPUFriend/blob/master/Instructions.md)准备适合自身系统模型的完整电源 plist，再在隔离目录生成：

```sh
./ResourceConverter.sh --kext /path/to/own-modified-power.plist
```

本机配置意图为全局 EPP64 并保留原 QoS，尚无独立性能或续航收益测量。该工具只生成数据载体；若停用 CPUFriend 与 Provider，应另记为不同配置。

## 4. 安装系统侧图形组件

| 组件 | 本机记录的配套 |
|---|---|
| EFI 中的 WhateverXe | 0.8.2-R16 |
| [WhateverXe-Graphics](https://github.com/b00t0x/WhateverXe-Graphics/releases/tag/v0.4.4) | Graphics 0.4.4、AppleIntelTGLCompat 0.8.1、ABI 1 |
| [NullMoth NVIDIA](https://github.com/nullmoth/nvidia-macos-driver/releases/tag/v3.0) | 3.0，包含其内核、Metal 配套及 GSP 固件 |

按各项目说明在 macOS 内安装并核对。构建 WEX 时生成的 Compat 不自动等于上述已记录配套；复制 EFI 也不会完成这些安装。

## 5. 检查与测试

```sh
python3 tools/verify_package.py
```

再用对应 OpenCore 构建的 `ocvalidate` 检查补齐依赖、填好标识后的副本。公开包检查是文件与配置检查，不是启动验收。

当前 Intel 负责内屏，NVIDIA 为 headless，高刷关闭。首次测试分别记录可见桌面、显示归属、驱动版本和 Metal 作业；不同会话结果按[历史记录](HISTORY.md)区分。

排查 Type-C 时可用[只读采集器](../tools/collect-usb-firmware/)。它读取当前 HS04／SS02 和固件属性，不复位端口、不控制 PD、EC 或 GPIO；缺失值保留为空，不记为0。
