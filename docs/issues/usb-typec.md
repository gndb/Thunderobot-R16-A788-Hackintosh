# USB-C映射与供电

更新：2026-11-16。默认根EFI使用UTBMap1.0.3，10个选定逻辑端口；HS15／HS16已移除。`port-count=20`表示最高端口索引。

## 当前映射

11月15日同一后置口实插：手机USB2位于HS04，换数据线后USB3.x位于SS02；电脑侧正反插均有记录。当前图将这两个口设为connector9，`kUSBCompanionIndex`为17／3；字段值与端口号4／18分别记录。

| 端口 | Connector | Companion字段 |
|---|---:|---:|
| HS01 | 3 | 未指定 |
| HS02 | 3 | 18 |
| HS03 | 3 | 19 |
| HS04 | 9 | 17 |
| HS06、HS07 | 255 | 未指定 |
| SS01 | 3 | 未指定 |
| SS02 | 9 | 3 |
| SS03 | 3 | 1 |
| SS04 | 3 | 2 |

其它USB-A配对保留当前保存值，未把未逐项重测的接线写成新验收。1401生成的bundle标识为`com.nullmoth.UTBMap`；名称变化不构成供电故障证据。再次导出后应比对companion字段，避免工具丢失自定义键。

## 供电问题

- 用户报告Windows和macOS均无法给正常手机充电；同口曾有USB3.x数据枚举。
- 电脑接受Type-C充电与电脑给手机供电分别记录。11月15日输入测试未报告外接电源，但缺同期PD合同、VBUS、EC Learn和ADPP值。

数据枚举、USBX电流预算和Windows电池状态不能替代PD角色、合同或保护反馈。跨系统异常使共用EC／PD／供电保护链值得优先核对，尚未定位故障器件。

## 诊断与历史

默认EFI保留666字节被动诊断AML，源码在[usb-firmware-diag](../../src/acpi/usb-firmware-diag/)；[采集器](../../tools/collect-usb-firmware/)读取`r16-usb-*`及HS04／SS02统计。旧HS02记录另列，不改名冒充HS04。缺失字段与全FF值保持不可用。

11月14日曾以HS02／SS02映射保留RHUB，macOS仍无连接；后续实插纠正了后置口定位。[旧报告](https://github.com/gndb/Thunderobot-R16-A788-Hackintosh/blob/5f8d2103d0674f057ef20e0acd65a85fa1ba7140/docs/issues/usb-typec.md)保留当时观察，不能继续作为当前配对依据。

当前修订已同步配置、配对和采集目标，尚未形成USB／PD完整运行验收。后续按同次启动分别取得输入、输出和数据状态；不由字段名称推断物理连线或直接试写EC／GPIO。
