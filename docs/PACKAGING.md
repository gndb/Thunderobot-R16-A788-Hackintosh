# 完整EFI包内容

当前仓库根`EFI/`与完整发行包包含同一份 **179文件EFI**，采用本机保存的原始文件及config。此次只移除不参与运行的6份备份：

- 3份`config.plist.nullmoth-usb-*`旧配置；
- 3份`UTBMap.kext.nullmoth-*`旧映射。

当前驱动、UEFI驱动、工具、OpenCanopy资源和R16主题均保留，不因打包改换二进制或关闭驱动。文件指纹见[完整清单](../metadata/assembly-manifest.json)和[分发清单](../metadata/distribution.json)。

## 取得与使用

从[发行页](https://github.com/gndb/Thunderobot-R16-A788-Hackintosh/releases)下载完整EFI包，或直接取得仓库根`EFI/`。解压后应有`EFI/BOOT/BOOTx64.efi`和`EFI/OC/config.plist`。当前包无需使用旧版扩展包再拼装驱动。

config按机主明确授权原样公开，保留原有SMBIOS、ROM和蓝牙状态。其他使用者建议换成自己的SMBIOS标识，再按[安装说明](INSTALL.md)测试。旧的63文件驱动扩展包属于历史发行，当前以179文件完整包为准。

Intel／NVIDIA的macOS系统侧组件不属于EFI目录，仍需按[版本表](../README.md#二系统与驱动版本)单独安装。文件齐全不改变当前显示恢复、供电及媒体兼容的验证范围。

## 来源与检查

各组件来源和版本见[依赖清单](../metadata/dependencies.json)，原版权与许可保留，未统一改成仓库MIT许可。已核对的四项官方驱动对应源码继续保留在[发行页](https://github.com/gndb/Thunderobot-R16-A788-Hackintosh/releases)，详情见[来源与许可](THIRD_PARTY.md)。

仓库中的`tools/verify_package.py`用于核对配置、文件及版本；`tools/assemble_efi.py`可按完整清单复制匹配文件。它们执行文件检查和组装，不代替实际启动测试。
