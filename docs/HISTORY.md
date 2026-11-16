# 版本与验证记录

主分支只保留当前根EFI和一份11月14日成功备份。清理前的完整仓库保存在标签 `archive/pre-cleanup-20261116`，对应固定提交 [5f8d210](https://github.com/gndb/Thunderobot-R16-A788-Hackintosh/tree/5f8d2103d0674f057ef20e0acd65a85fa1ba7140)。旧实验档可从该提交下载，无需在当前目录重复保存载荷。

## 会话与配置

| 日期／档案 | 版本与结果 | 入口 |
|---|---|---|
| 11月16日当前部署 | WEX0.8.2-R16；USB映射1.0.3、HS04／SS02配对17／3；AirportRTW2.3.3依赖；完整运行验收待补 | [EFI](../EFI/)、[当前元数据](../metadata/current.json) |
| 11月14日15:49成功会话 | WEX0.8.2／Graphics0.4.4／Compat0.8.1／NV3.0；桌面60Hz、连续亮度、Intel1024元素回读0错、NV四模块加载 | [成功备份](../profiles/usable-20261114/)、[验证摘要](../metadata/validation-20261114.json) |
| 11月14日USB诊断档 | 成功基线上增加666字节被动诊断AML；当时写入后未取得新macOS属性输出 | [归档配置](https://github.com/gndb/Thunderobot-R16-A788-Hackintosh/tree/5f8d2103d0674f057ef20e0acd65a85fa1ba7140/profiles/experimental-usb-firmware-20261114) |
| 11月13日05:27七项作业 | WEX0.8.0／NV2.7.2；两卡基础离屏作业 | [精确配置](https://github.com/gndb/Thunderobot-R16-A788-Hackintosh/tree/5f8d2103d0674f057ef20e0acd65a85fa1ba7140/profiles/dual-gpu-verified-0527)、[结果JSON](../metadata/dual-gpu-tests.json) |
| 11月13日旧根／核显独立档 | 旧公开快照及保留`-nvoff`的核显路线 | [旧根](https://github.com/gndb/Thunderobot-R16-A788-Hackintosh/tree/5f8d2103d0674f057ef20e0acd65a85fa1ba7140/profiles/historical-20261113)、[核显独立](https://github.com/gndb/Thunderobot-R16-A788-Hackintosh/tree/5f8d2103d0674f057ef20e0acd65a85fa1ba7140/profiles/igpu-only-20261113) |

11月13日七项包括：两卡各做256元素整数计算、16×16纹理清屏回读、三角形绘制回读，再由同一进程向两卡独立队列提交作业。记录零差异、零超时；双队列末元素分别1037／2037。测试源码在[metal-smoke](../src/metal-smoke/)。它没有跨GPU共享资源，也未测执行重叠。

新版没有重跑上述七项，不把11月13日结果归入11月14日或11月16日。所有版本仍保留显示恢复、完整媒体能力和长期可靠性的验证缺口。

## 归档材料

- [旧0.8.0源码与构建对应](https://github.com/gndb/Thunderobot-R16-A788-Hackintosh/tree/5f8d2103d0674f057ef20e0acd65a85fa1ba7140/src/WhateverXe-0.8.0-R16-historical)
- [11月14日原报告](https://github.com/gndb/Thunderobot-R16-A788-Hackintosh/blob/5f8d2103d0674f057ef20e0acd65a85fa1ba7140/docs/CURRENT_REPORT_20261114.md)和[当时的问题表](https://github.com/gndb/Thunderobot-R16-A788-Hackintosh/blob/5f8d2103d0674f057ef20e0acd65a85fa1ba7140/docs/ISSUES_20261114.csv)

历史报告中的后置HS02定位已由11月15日实插纠正为HS04；历史原文保留当时认知。此前Shared修卷没有恢复已损坏报告的正文，那些材料不作为运行成功或GPU根因证据。
