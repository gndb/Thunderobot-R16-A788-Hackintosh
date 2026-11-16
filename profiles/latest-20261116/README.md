# 11月16日：最新部署快照（USB 实验版）

这份配置来自11月16日00:24 UTC直接读取的macOS硬盘EFI。完整私有备份留在Shared；本目录公开脱敏配置和允许分发的部分载荷，**不是完整即用EFI**。

- 保留 WEX 0.8.2-R16 二进制、亮度补丁、现有电源及图形配置；高刷保持关闭。
- 当前磁盘中的 AirportRTW 为 **2.3.3**，仅在[依赖清单](dependencies.json)列出版本和文件指纹，不在本包分发无线驱动。
- UTBMap **1.0.3**：保留10个逻辑端口，删除HS15/HS16。后置Type-C为HS04/SS02，connector=9，companion索引17/3；普通USB-A为connector=3，内部设备为255。端口总数上限字段20表示最高索引，不是启用了20个端口。
- 保留先前只读USB固件诊断AML及补丁；本次没有新增EC、SMI或PD写命令。

最新USB修订后尚未形成完整的macOS同次启动验收记录。此前两系统的手机无充电问题仍未解决；端口枚举和高速数据成功不代表Type-C供电或PD合同正常。见[最新状态报告](../../docs/issues/usb-typec-20261116.md)。

[11月14日成功基线](../usable-20261114/README.md)单独保留，根EFI仍指向该基线。本快照不继承其桌面、计算或亮度成功结论。冷启动黑屏、熄屏唤醒和USB-C/PD仍是未解决问题。

按[安装说明](../../docs/INSTALL.md)补齐本档[依赖](dependencies.json)、自己的SMBIOS及本机生成的CPUFriend数据。系统侧Intel/NVIDIA组件需要单独安装，不能通过复制EFI完成。

源码继续使用[src/WhateverXe](../../src/WhateverXe/)中固定的0.8.2上游和R16补丁；二进制与11月14日一致。本次没有新的显卡源码改动。
