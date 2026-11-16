# 来源与许可

本仓库新增说明、配置整理和工具按根目录[MIT](../LICENSE)提供。第三方内容保留各自许可、版权及SPDX声明。

| 内容 | 来源与许可 |
|---|---|
| OpenCore核心和收录UEFI驱动 | acidanthera/OpenCorePkg，保留[BSD-3-Clause](../licenses/OpenCore-BSD-3-Clause.txt) |
| WhateverXe源码与二进制 | 官方0.8.2固定提交及R16补丁，保留[源码许可](../src/WhateverXe/LICENSE.txt)、[二进制许可副本](../licenses/WhateverXe-BSD-3-Clause.txt)与逐文件声明；个别Compat文件为BSD-2-Clause |
| AuxKC原生shell候选 | 沿用WhateverXe-Graphics工具的[BSD-2-Clause](../contributions/auxkc-upstream/LICENSE.txt) |
| AuxKC独立Python工具 | 目录中的MIT许可 |
| SSDT、UTBMap、USB采集器 | 本机适配与工具材料，保留来源及接口范围 |

扩展发行包为可再分发组件保留各自许可、通知和必要的对应源码；完整文件集与缺项分别见[打包说明](PACKAGING.md)。GPL／APSL组件的对应源码附在同一发行页。仓库根EFI仍是20文件配置子集，扩展包收录情况见[分发清单](../metadata/distribution.json)。

本机CPUFriendDataProvider为纯plist配置，未发现个人身份，随扩展包提供；它只对应本机记录的电源策略，其他硬件应按[使用步骤](INSTALL.md)生成自己的数据。其它组件和资源按[当前依赖](../metadata/dependencies.json)或[成功备份依赖](../profiles/usable-20261114/dependencies.json)从原项目取得。

仓库不包含Apple恢复／安装镜像、Graphics donor、GPUBundles、系统dylib／缓存，以及Apple网络／音频donor或SimpleHDA涉及的系统材料。

公开配置清除机器序列、MLB、UUID、MAC及蓝牙私有状态；原始IORegistry、NVRAM、sysdiagnose、整盘镜像和私有恢复资料不发布。固定协议GUID和二进制构建UUID用于核对版本，予以保留。

旧版本源码和载荷在[归档提交](HISTORY.md)中继续保留原许可；目录精简不改变其许可。
