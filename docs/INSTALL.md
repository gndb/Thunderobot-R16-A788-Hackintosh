# 使用步骤

先阅读[硬件范围](HARDWARE.md)、[功能状态](STATUS.md)和[依赖表](DEPENDENCIES.md)。本机可用实验基线不是全功能安装镜像；USB实验档也不是成功配置的替代品。

## 1. 选择同一版本的档案

- 默认`EFI/`与`profiles/usable-20261114/EFI/`对应11月14日15:49可用实验基线。
- `profiles/experimental-usb-firmware-20261114/EFI/`在该基线上另加USB只读固件诊断，尚未取得本机macOS属性输出。
- 11月13日历史profile保留各自旧公开载荷；不要与新的根EFI混用。历史版本的精确依赖和测试范围保持。

## 2. 在离线副本中补齐依赖

保留自己的完整EFI和恢复入口，把本仓库公开内容合并到新的测试副本。补齐该profile依赖表中所有启用的kext、UEFI驱动和资源；本仓库有意没有把全部第三方或系统侧材料打包。

CPUFriendDataProvider不随新版公开包分发。若保留CPUFriend两条启用配置，须按[CPU政策](CPU_POLICY.md)从自己取得、适用于该系统模型的数据生成Provider并核对路径。若选择停用这两条配置，应记录为不同的测试配置，不再把结果当作原基线完整复现。

禁用的Apple网络donor/WhateverGreen条目不表示需要恢复它们，也不表示当前产生了新功能。不要重新放入历史`WhateverXe.before-*`、旧config或试验备份。

## 3. 填入自己的SMBIOS

公开配置中的SystemSerialNumber、MLB、SystemUUID留空，ROM为六个零字节；使用者必须自行生成并填入自己的值。公开配置去掉蓝牙控制器私有NVRAM。产品模型记录为MacBookPro16,2。

参考[GenSMBIOS](https://github.com/corpnewt/GenSMBIOS)和[OpenCore文档](https://github.com/acidanthera/OpenCorePkg/tree/master/Docs)。不要将别人的真实标识并入自己的配置。

## 4. 单独完成系统侧图形依赖

新版EFI中WEX为0.8.2-R16；15:49成功会话的系统侧组合为Graphics0.4.4、AppleIntelTGLCompat0.8.1、Graphics ABI1、NVIDIA3.0。它们不等于放进EFI的kext集合，必须在macOS内按相应项目说明安装和核对。

- [WhateverXe-Graphics](https://github.com/b00t0x/WhateverXe-Graphics/releases/tag/v0.4.4)：系统侧Graphics配套；本仓库不分发Apple donor和系统dylib。
- [NullMoth NVIDIA v3.0](https://github.com/nullmoth/nvidia-macos-driver/releases/tag/v3.0)：系统侧NVRM/NVAccel/NVRMFB/NVRMAGDC、Metal配套和固件，按原项目取得。
- 构建WEX源码可能同时得到Compat产物；它不自动等于已验证的系统侧Compat。不要仅因新构建生成了一个Compat就覆盖现有配套。

这些版本说明保存本机对应关系，不保证其他系统版本、固件或面板可直接使用。不能只复制EFI就声称复现完整图形加速。

## 5. 检查与第一次测试

运行`python3 tools/verify_package.py`核对公开包的脱敏、文件指纹、档案和证据范围。再用匹配OpenCore构建的ocvalidate检查补齐依赖、填好自己标识后的副本。公开包检查通过不代表第三方依赖已自动下载或其它机器可启动。

可用基线高刷关闭，核显负责内屏，NVIDIA为headless。分别记录桌面、显示归属、驱动版本和Metal结果。七项旧双GPU作业不能代替新版本测试；OpenCore的EXITBS也不等于后续内核阶段已成功。

只排查USB时使用实验profile说明及只读采集器，保留每次启动的对应关系。它不会复位端口、切换PD、调用EC/GPIO供电方法或修改EFI。没有属性应记录为未取得，不能替换成0。
