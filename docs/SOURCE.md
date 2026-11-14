# WEX源码、补丁与二进制对应

当前默认公开WEX是本机0.8.2-R16。历史0.8.0源码与载荷分开保留，不把旧源码目录描述成新二进制的精确编译输入。

## 新版来源

| 项目 | 值 |
|---|---|
| 官方基底 | [WhateverXe 0.8.2固定提交](https://github.com/b00t0x/WhateverXe/commit/4512191b9643e2391431fbd9639305b61568ee32) |
| 上游commit | `4512191b9643e2391431fbd9639305b61568ee32` |
| R16生产补丁 | [13路径生产patch](../patches/wex-0.8.2-r16/R16-on-WhateverXe-0.8.2-production.patch) |
| 测试适配 | [11路径测试patch](../patches/wex-0.8.2-r16/R16-0.8.2-test-fixture-adaptation.patch) |
| 新源码树 | [src/WhateverXe](../src/WhateverXe/) |
| WEX可执行文件SHA256 | `515f9399e72d7a761cd5bde32dfcb92d23be97e671f2d4ca5ec2ffa7db6a6d1a` |
| Mach-O构建UUID | `854C7BE0-5CE6-3960-BC84-5AB44C52D5E5`，二进制身份，不是电脑SystemUUID |

来源、重放和文件清单见[新来源元数据](../metadata/20261114/source-provenance.json)。本次已对固定官方源码执行两补丁的`git apply --check`及实际应用，均成功。发布包中的WEX与本机可信读回的可执行文件SHA一致。

**这些检查证明补丁可重放、配套二进制身份一致。本轮没有重新编译出相同二进制，也未找到同次完整编译输入清单；不称逐字节构建复现。**

## 修改范围和贡献边界

新版保留本机设备/目标门禁、R5/R6输出与加速器语义诊断、首次接管相关路径、软件媒体能力规避和背光64位算术补充。各项不是都完成了独立硬件A/B验收，也不表示所有A788平台通用。

上游已存在[保留固件布线并延后激活的机制](https://github.com/b00t0x/WhateverXe/commit/37580ea572c8858c3a584aea9a58e9c60f102ca9)。本机案例和定向差异应与已有上游机制区分。背光算术与AuxKC成员保留各自拆分审查；显示恢复、USB、用户态加载问题保留为独立报告，不把全部本机改动合成一个无法验证的修复声明。

R10/R11恢复试验和高刷没有归入本次成功结论；媒体软件规避也不等于硬件视频编解码已完成。

## 构建和测试

从固定上游提交开始，按`patches/wex-0.8.2-r16/series`顺序应用补丁。公开源码保留原构建入口，另行准备其要求的[Lilu](https://github.com/acidanthera/Lilu)和[MacKernelSDK](https://github.com/acidanthera/MacKernelSDK)。构建工具链、依赖和选项应记录到新的构建清单；不要假定更换工具链还会生成相同SHA。

可运行的测试与实际执行结果分别记录。历史216项CPU检查、15,597,568组算术计数的部分详细日志已缺失，不能冒称本轮新跑。

本轮另外完成[背光64位host检查](../contributions/backlight64/)：测试header与生产源SHA一致，在Linux/Clang x86_64上实际执行旧/新23字节指令窗口，589,824组算术输入、1,769,589项检查，退出0。它验证该算术窗口及测试关系，不证明本机门禁/可达路径或硬件所有亮度场景。上游main缺少该功能依赖的R16 native-fallback/R5/R6可达链，因此本次作为自仓独立贡献保存，没有把它作为单独上游PR。详见[贡献状态](CONTRIBUTIONS.md)。

构建脚本得到的Compat产物不能自动覆盖已验证系统侧Compat。Apple donor和系统dylib不属于公开自定义源码树的再分发内容。

## 旧0.8.0档案

[历史源码](../src/WhateverXe-0.8.0-R16-historical/)对应WEX SHA `7d7ee576fe84cc47919060a454d1b50bb718f54ee7b1872fb53fc20d2af2316a`，构建UUID `1C8BA045-8284-362F-9D61-3459AE2801A1`。它与原11月13日档案、旧编译输入清单和七项作业保持原有对应关系，不随新版文档升级为0.8.2。

历史参考包括原上游`db438fdf4d5fe903f5dfbc65537ed3884e2ea980`及经选择的HX/时钟参考；逐文件来源、版权和SPDX保留。辅助测试中固定输出位置可以参数化，但不得因此修改已验二进制后沿用原SHA。

主BSD-3-Clause、个别文件BSD-2-Clause和各来源注释保留，详见[THIRD_PARTY](THIRD_PARTY.md)。
