# 来源与许可

本仓库新增说明、配置整理和自有工具按根目录[MIT](../LICENSE)提供。完整EFI内的第三方文件保留各自版权、许可及SPDX声明，仓库MIT不延伸为对所有载荷的重新授权。

| 内容 | 来源与声明 |
|---|---|
| OpenCore核心及其开源UEFI组件 | acidanthera/OpenCorePkg，[BSD-3-Clause](../licenses/OpenCore-BSD-3-Clause.txt) |
| WhateverXe源码与二进制 | 官方0.8.2固定提交及R16补丁，[源码许可](../src/WhateverXe/LICENSE.txt)、[二进制许可副本](../licenses/WhateverXe-BSD-3-Clause.txt)及逐文件声明 |
| HfsPlus／apfs_aligned及OpenCanopy资源 | [OcBinaryData](https://github.com/acidanthera/OcBinaryData)，独立载荷不自动采用OpenCore的BSD许可 |
| SimpleHDA | [作者v1.0.1 NOTICE](https://github.com/laobamac/SimpleHDA/blob/v1.0.1/NOTICE.md)；包含原AppleHDA组件及其原有权利声明 |
| NullMothSafe | [1401 v2.7.2](https://github.com/nullmoth/1401/tree/v2.7.2)，PolyForm Noncommercial及原通知 |
| 其它kext与本机电源数据 | 精确版本、文件指纹及原项目见[依赖清单](../metadata/dependencies.json) |
| 独立贡献与工具 | [backlight64](../contributions/backlight64/)、[AuxKC shell](../contributions/auxkc-upstream/)、[AuxKC Python](../tools/auxkc/)保留各目录许可 |

AirportRTW V2.3.3、RealtekBluetoothFirmware v1.0.2、VoodooPS2Controller2.3.7和RTL8111 v3.0.0已有逐文件匹配官方包的记录，对应固定源码、许可和固件通知保留在[发行页](https://github.com/gndb/Thunderobot-R16-A788-Hackintosh/releases)。其它本机文件的出处与已确认程度按清单记录，不把相近版本源码当作精确对应源码。

本次按机主要求发布完整179文件EFI，保留原config及身份字段，排除6份旧配置／映射备份。原始IORegistry、完整NVRAM转储、sysdiagnose、整盘镜像和其它本地恢复资料不在此EFI包内。Apple安装镜像、系统侧Graphics donor、GPUBundles及系统缓存也不属于此包。

旧版本源码与载荷仍可从[归档索引](HISTORY.md)恢复，原许可继续保留。包内范围见[打包说明](PACKAGING.md)。
