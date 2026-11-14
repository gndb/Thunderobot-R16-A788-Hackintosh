# 来源、许可与发布范围

自有说明、配置整理和新工具按根目录MIT许可；第三方源码、二进制、固件与系统材料仍适用各自许可，不能统一改成MIT。

- OpenCore核心及收录的OpenCore UEFI驱动：acidanthera/OpenCorePkg，BSD-3-Clause；保留`licenses/OpenCore-BSD-3-Clause.txt`。
- 新WEX树基于官方0.8.2固定提交，保留`src/WhateverXe/LICENSE.txt`和逐文件版权/SPDX。R16生产与测试补丁随来源说明提供。
- 历史0.8.0树独立保留许可与参考来源。源码中个别Compat文件为BSD-2-Clause，依照文件声明；这些自定义源码不是Apple donor二进制。
- SSDT、UTBMap和新只读USB采集器是本机适配/工具材料；需按本机路径、表范围和接口重核，不能因设备ID相同就复制机器特定地址。
- CPUFriend依赖按原项目取得；本仓库提供政策说明和生成方法，不分发来源未核齐的完整本机电源XML数据块。
- AuxKC原生shell上游候选沿用WhateverXe-Graphics工具的BSD-2-Clause许可，见`contributions/auxkc-upstream/LICENSE.txt`；独立Python候选检查器按其MIT许可，不分发Apple bundle或内核缓存。

其它第三方kext、OpenCanopy图像和固件合集按[依赖表](DEPENDENCIES.md)取得。Apple恢复/安装镜像、Graphics donor安装载荷、GPUBundles、系统dylib、系统缓存、Apple网络/音频donor及SimpleHDA涉及的系统材料不进入本仓库发布包。

不公开完整旧EFI、identity/residual、整盘或分区镜像、原始IORegistry/NVRAM/sysdiagnose、个人路径/序列/网络身份和私有恢复控制器。问题材料采用白名单摘要及必要调用栈片段；二进制构建UUID与固定协议GUID保留以供复核。

已损坏报告及旧损坏机器索引不作为源码、运行成功或上游缺陷证据。协作资料修复经过只作维护附录，不能推导GPU根因或物理介质健康。
