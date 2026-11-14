# 后置Type-C：正确映射仍无连接

状态：数据与输入充电仍未解决。新只读固件诊断已部署，但尚无本机macOS属性输出，不作为USB修复发行。

## 可重复核对的事实

| 项目 | 结果 |
|---|---|
| 控制器 | PCH Intel8086:7A60，PCI功能0x14,0 |
| 后置口 | HS02=2、SS02=18，companion关系与Windows设备使用记录对应 |
| 端口类型/映射 | connector9，12个活动逻辑口；port-count0x14是最高索引，不是20个活动口 |
| Windows | 同硬件数据连接可用；同Type-C充电器和线材可给电脑充电 |
| RHUB实验 | 停用USB-Reset并加`-utbacpioff`；实际参数、ACPIPlane的RHUB/HS02/SS02及映射均已生效 |
| 15:20macOS观察 | 数据设备连接着仍无反应；两目标口连接、枚举失败与过流计数均0 |

这些事实足以记录RHUB保留实验失败，暂不足把问题归为USBToolBox缺陷或已知EC/PD根因。USBToolBox1.2.0的Tahoe字段已实际出现，重新改同一映射没有新增依据。

## 新实验档

[USB实验profile](../../profiles/experimental-usb-firmware-20261114/README.md)只在精确本机表范围内包裹XHCI设备方法，将PPOE、UCMS、PSG1/PSG2、POVP、XDCE、可选DTFS和PDPG存在状态发布为属性。其它UUID/revision请求透传原方法。

[采集器](../../tools/collect-usb-firmware/)读取PCI层`r16-usb-*`及HS02/SS02统计。属性缺失与8字节全FF均记不可用，不能替换成0；真实数值0则保留。离线回放和模拟只证明解析/分派逻辑，不证明本机已发布属性或恢复连接。

## 不可推断的内容

Suspended不是VBUS电压测量，USBX电流不是PD合同，PSG1/PSG2是固件参数而非测得的GPIO电平。父控制器电源块与Type-C充电不能凭方法名等同。严格限定的OEM重复对象改名已试失败，不能把相同改动再包装成新修复，也不据此直接写GPIO或伪造接电状态。

下一步先取得同一次启动的被动属性、端口统计与实际接线说明，再缩小角色/父控制器初始化分支。数据、给电脑输入充电、DP输出与TB/USB4分别验收。
