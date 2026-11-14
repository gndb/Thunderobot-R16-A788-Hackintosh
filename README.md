# 雷神 R16 · Intel A788 与 RTX 5080 黑苹果适配记录

**i9-13900HX / Intel UHD A788 / RTX 5080 Laptop / BOE NE160QDM-NZL**

2026-11-14。本次公开11月14日15:49成功会话对应的可用实验基线：WEX0.8.2-R16、系统侧Graphics0.4.4 / Compat0.8.1和NVIDIA3.0。内屏60Hz、连续亮度及Intel小型计算已有成功记录；冷启动可靠性、熄屏唤醒、USB-C/PD和媒体兼容仍有问题。

**这里分发的是脱敏配置、部分载荷、源码和证据摘要。补齐第三方依赖及自己的SMBIOS后才能组成测试EFI；仅复制EFI不能完成系统侧图形驱动安装。**

## 选择档案

| 档案 | 定位 | 验证范围 |
|---|---|---|
| [EFI/](EFI/OC/config.plist) / [usable-20261114](profiles/usable-20261114/README.md) | 11月14日15:49可用实验基线 | 单次桌面、连续亮度、Intel1024元素GPU计算/回读0错；NV3.0四模块加载、headless。未重跑七项双GPU作业 |
| [USB诊断实验版](profiles/experimental-usb-firmware-20261114/README.md) | 在可用基线上另加只读固件属性诊断 | 17:11已写入本机EFI；尚未取得macOS属性输出，不是USB修复版 |
| [11月13日历史载荷](profiles/historical-20261113/EFI/) | 保存原公开根EFI | WEX0.8.0 / NV2.7.2的原有对应关系不变 |
| [精确七项双GPU历史档](profiles/dual-gpu-verified-0527/EFI/OC/config.plist) | 11月13日05:27对应配置 | 原七项基础离屏作业；不借用新版根EFI的WEX载荷 |
| [核显独立历史档](profiles/igpu-only-20261113/EFI/OC/config.plist) | 早前核显路线 | 保留`-nvoff`；与新的双GPU/USB实验档分开 |

各有日期的profile保留自己的公开载荷或明确来源，仍需补齐该档依赖。不可把旧config与新版WEX随意混用，也不能把实验档当作已验收配置。

## 本次更新

- 新版R16生产补丁和测试适配补丁已在官方0.8.2固定提交上重放；公开WEX二进制与本机读回相同。源码可重放不代表已重新编译得到相同二进制。
- [成功配置、USB实验配置和历史配置](docs/CONFIGURATION.md)分别记录；身份字段及蓝牙控制器私有NVRAM已清理，禁用的donor条目不作为新增功能。
- [USB固件采集器](tools/collect-usb-firmware/)读取PCI层诊断属性与HS02/SS02统计；缺值不当作0，尚未在本机macOS进行新一轮采集。
- [问题专题](docs/issues/README.md)区分内核/显示、USB、双GPU会话、WebKit沙盒和BetterDisplay应用崩溃。
- [独立贡献](docs/CONTRIBUTIONS.md)包括背光算术检查、AuxKC候选和测试。AuxKC上游仅允许协作者创建PR，已保存在自己的fork和本项目；本次未创建上游PR。

## 机器与状态

| 项目 | 本机记录 |
|---|---|
| 整机 / 主板 / BIOS | THUNDEROBOT R16 / NLYA / AMI TP181 |
| CPU / 内存 | Intel Core i9-13900HX；48GiB DDR5 |
| 核显 / 独显 | Intel UHD `8086:A788` rev04 / RTX 5080 Laptop `10DE:2C19` |
| 内屏 | BOE NE160QDM-NZL，2560×1600；当前60Hz，高刷关闭 |
| 记录系统 | macOS报告26.7.2（25G332），Darwin25.6.0 |

完整硬件范围见[HARDWARE](docs/HARDWARE.md)。同名R16和相同设备ID都不保证具备相同固件、接口接线或面板。

已成功、未解决与暂停项目见[STATUS](docs/STATUS.md)。七项旧双GPU案例与新版单Intel计算按[会话矩阵](docs/issues/dual-gpu-sessions.md)分开，不能组合成一次完整新版验收。

## 使用与源码

1. 阅读[安装步骤](docs/INSTALL.md)和[依赖表](docs/DEPENDENCIES.md)，在新的离线副本中补齐载荷。
2. 填自己的SMBIOS标识；需要CPUFriend时按[CPU政策与生成方法](docs/CPU_POLICY.md)生成自己的DataProvider。
3. 按[源码来源](docs/SOURCE.md)核对WEX版本、固定上游提交、补丁和二进制指纹。
4. 运行`python3 tools/verify_package.py`检查公开包，再用匹配OpenCore构建的ocvalidate检查补齐后的副本。离线检查不代表硬件启动成功。

自有说明与工具按[MIT](LICENSE)提供；WEX、OpenCore及其他内容保留各自许可，详见[第三方来源](docs/THIRD_PARTY.md)。本仓库不包含Apple系统/donor安装载荷、macOS安装镜像、原始NVRAM/IORegistry或机器身份。
