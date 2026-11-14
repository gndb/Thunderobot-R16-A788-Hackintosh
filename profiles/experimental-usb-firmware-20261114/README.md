# USB固件状态诊断实验档

本档在[11月14日可用基线](../usable-20261114/README.md)上增加666字节只读诊断SSDT及一条精确DSDT方法改名。17:11已写入本机EFI，但尚未取得macOS新属性输出；它不是已验收USB修复，也不是额外成功启动记录。

作用是把固件已有PPOE/UCMS等枚举快照公开到PCI属性，原生其它请求透传。新诊断分支不新增EC/GPIO/PD控制调用；读取沿用原OperationRegion/全局锁语义。只适用于已核对的本机表范围，不全局重命名其它设备方法。

按[USB专题](../../docs/issues/usb-typec.md)理解已失败的RHUB实验与缺失证据，运行[一次性采集器](../../tools/collect-usb-firmware/)保存PCI属性和端口统计。没有属性不等于0，FF*8为不可用。固件字段不是VBUS或PD合同测量。

使用前仍需补齐[依赖](../../docs/DEPENDENCIES.md)、自己的SMBIOS和DataProvider。测试时保留与可用基线分开的恢复入口；不要与高刷、旧GPIO电源表或R10/R11同时混改。
