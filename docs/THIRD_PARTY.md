# 来源、许可与发布范围

仓库中的自有说明、配置整理与工具按根目录 MIT 许可提供；第三方内容仍适用原许可。

- OpenCore 核心及收录的三个 OpenCore UEFI 驱动：acidanthera/OpenCorePkg，BSD-3-Clause；原许可见 `licenses/OpenCore-BSD-3-Clause.txt`。
- 自定义 WhateverXe：基于 b00t0x/WhateverXe，BSD-3-Clause；原许可在 `src/WhateverXe/LICENSE.txt`。保留各源文件已有的版权、SPDX 和参考 fork 说明。
- 源码快照内 AppleIntelTGLCompat 个别文件标 BSD-2-Clause，依照文件原文；它们不是 Apple 原始 donor 驱动。
- 本机 SSDT 和 UTBMap 是从本机配置提取的适配材料；其他机型使用前需要重做路径与端口核对。

其余共享 kext、固件、Apple donor 和 OpenCanopy 图像资源不随本包再分发。所需项目、版本及精确文件哈希在 `docs/DEPENDENCIES.md` 和 `metadata/dependencies.json`；GPL/APSL、固件及系统材料应按原项目许可取得，不能将本仓库 MIT 许可套用于它们。

本项目没有上传 macOS 安装器、恢复映像、系统框架或 Apple 专有驱动，也没有提供整机系统镜像。
