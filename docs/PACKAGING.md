# 包内容、完整组装与隐私

## 选择哪个包

| 内容 | 文件范围 | 用途 |
|---|---|---|
| 仓库根`EFI/`／配置包 | 20个公开基础文件 | 查看配置、源码对应关系和USB映射 |
| 驱动扩展包 | 63个EFI文件，另附4份对应源码及许可 | 已补入多数可再分发驱动；仍需补齐下表项目 |
| 本地完整组装 | 179个实际使用文件 | 从自己的匹配EFI或原作者文件组装，不混入旧备份 |

完整清单：[assembly-manifest.json](../metadata/assembly-manifest.json)；公开扩展包清单：[distribution.json](../metadata/distribution.json)。文件齐全以后仍需填写自己的SMBIOS，Intel／NVIDIA系统侧组件也需另外安装。

扩展包新增Lilu、CPUFriend及本机DataProvider、AppleALC、BrightnessKeys、CpuTopologyRebuild、RestrictEvents、VirtualSMC及插件、AirportRTW、RealtekBluetoothFirmware、RTL8111、PS/2驱动等。原二进制未因打包而修改。

AirportRTW V2.3.3 Tahoe、RealtekBluetoothFirmware v1.0.2、VoodooPS2 2.3.7、RTL8111 v3.0.0均已逐文件匹配官方发行包，并在同一发行页提供固定提交的源码。**RTL8111发行号v3.0.0的内部CFBundleVersion原本就是3.0.4**，这两个版本标签并不冲突。

## 为什么公开扩展包仍有缺项

| 项目 | 本轮结论与取得方式 |
|---|---|
| SimpleHDA 1.0.1 | [作者NOTICE](https://github.com/laobamac/SimpleHDA/blob/v1.0.1/NOTICE.md)明确内置专有AppleHDA；从原作者或自己的安装资料取得 |
| HfsPlus、apfs_aligned | 未把OpenCore的BSD许可套用到这些独立固件驱动；从[原项目](https://github.com/acidanthera/OcBinaryData/tree/master/Drivers)或自己的EFI取得 |
| AMFIPass、ECEnabler、USBToolBox kext | 本轮未取得这些具体载荷的明确再分发授权；按[依赖来源](../metadata/dependencies.json)取得 |
| BlueToolFixup 2.7.3、NVMeFix 1.1.4 | 最接近的官方发行与本机文件不同，尚未取得精确对应源码 |
| VoodooI2C／VoodooI2CHID 2.9.1 | 官方同版本RELEASE与DEBUG均未匹配本机文件，不能只按版本号替换 |
| OpenCanopy资源／R16主题 | 原作者资源与本机主题分别核对；本轮未统一确认全部资源的再分发范围 |

这是一份本次文件审查结果；“尚未取得授权或对应源码”不等于断言作者永远不允许再分发。驱动的公开下载地址、源码可见性和再分发许可是不同的信息。

## 一条命令组装完整文件集

从仓库根目录指定所需的原作者ZIP，或已经解压的匹配EFI目录：

```sh
python3 tools/assemble_efi.py --source /path/to/driver.zip --source /path/to/own-EFI --output /path/to/new-EFI
```

也可把扩展包ZIP作为一个`--source`；多个ZIP分别重复此参数，目录来源则应先解压。程序用SHA256和大小匹配文件，不执行来源里的程序、不修改原件；来源ZIP的目录结构不必相同。缺项会列出且不创建输出，不会默默关闭缺失驱动。某些本机定制文件未匹配公开发行，因此普通下载包不一定足够；此时需使用精确匹配的已有文件。

输出使用仓库内的脱敏config，忽略来源里的个人config和旧备份。填好自己的SMBIOS后，按[安装说明](INSTALL.md)检查和测试。这是当前配置的精确文件组装，不是为其他硬件自动生成适配。

## 隐私：只需处理少数身份字段

本机保存EFI未发现账号密码、访问令牌或私钥字段，风险不应等同于密码泄漏。但不能由“虚拟Mac”推断每个值都是虚构的：`ROM`可来自网卡地址，也可随机生成；序列号、MLB和UUID也可能已经用于苹果服务。[OpenCore服务配置说明](https://dortania.github.io/OpenCore-Post-Install/universal/iservices.html)

本次检查中ROM带本地管理位、UUID为v4，符合生成身份特征；现有Windows资料无法进一步证明它们全部虚构或从未被使用。公开副本继续只清理：

- `SystemSerialNumber`、`MLB`、`SystemUUID`和`ROM`；
- 蓝牙私有缓存；
- 3份旧config及3份旧USB映射备份，原件仍保留在本地恢复快照。

硬件型号、PCI ID、USB端口映射、固定协议GUID、构建UUID及不含个人信息的电源配置保留。CPUFriendDataProvider在本机是纯plist数据，隐私审查未发现身份字段，因此已纳入扩展包。

本机完整179文件包另存Shared供本人恢复，保留原有身份，不作为公开发行附件。公开扩展包使用清理后的身份模板；打全驱动与公开个人身份无需绑定。
