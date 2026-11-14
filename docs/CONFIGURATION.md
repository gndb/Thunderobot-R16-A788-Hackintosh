# 配置档案与差异

默认`EFI/`是11月14日15:49可用实验基线的脱敏公开子集。`profiles/usable-20261114/EFI/`保留同一档案；两者都须补齐依赖和自己的SMBIOS，不能直接当完整启动盘覆盖。

## 新旧差异

| 项目 | 新版可用基线 | 边界 |
|---|---|---|
| WEX | 0.8.2-R16，对应新版生产/测试patch | 系统侧Graphics/Compat仍另装 |
| NVIDIA | 系统侧3.0；`nvrmtgp=1`作为配置差异 | 开关存在不等于功耗或性能收益证明 |
| CPUFriend | 1.3.0与本机Provider记录1.0.1，限Darwin25 | 只记录EPP64政策；原Provider数据块不公开，须自行生成 |
| USBReset | 原表条目关闭，保留`-utbacpioff` | RHUB保留实验已生效仍失败，不称USB修好 |
| ACPI/USB映射/UEFI/quirks | 既有10份AML、UTBMap、UEFI驱动、quirks与DeviceProperties未新增改变 | 不重包装成新的通用优化 |
| 高刷/恢复试验 | 240/300Hz关闭；R10/R11不并入成功范围 | 未完成冷启动与熄屏可靠性验收 |

## USB实验档增量

`profiles/experimental-usb-firmware-20261114/EFI/`在可用基线上新增666字节只读SSDT和一条精确DSDT方法改名。它把PPOE/UCMS等固件枚举快照发布为`r16-usb-*`，其余请求保留原方法处理。新分支不新增EC/GPIO/PD控制调用，读取仍沿用原固件OperationRegion/全局锁语义。

17:11已在本机写入，但尚无新macOS属性输出；实验档不是USB修复版。DSL/AML、匹配表范围和采集说明随实验档一起提供，不能全局重命名其它设备的`_DSM`。

## 脱敏与保留

公开配置清空MLB、SystemSerialNumber、SystemUUID，ROM为六个零字节，并移除蓝牙控制器私有NVRAM。固定OpenCore命名空间、Apple属性协议GUID和Mach-O构建UUID保留；它们不是电脑身份。

旧11月13日profile使用自己的历史公开载荷，不再共用新的根WEX。禁用donor和历史备份不成为发布依赖。系统侧安装、本机数据块和完整原始日志的边界见[安装步骤](INSTALL.md)及[来源说明](THIRD_PARTY.md)。
