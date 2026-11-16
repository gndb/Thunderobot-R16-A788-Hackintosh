# 源码、构建与贡献

## WhateverXe 0.8.2-R16

| 项目 | 位置或指纹 |
|---|---|
| 官方基底 | [4512191b9643e2391431fbd9639305b61568ee32](https://github.com/b00t0x/WhateverXe/commit/4512191b9643e2391431fbd9639305b61568ee32) |
| 当前源码 | [src/WhateverXe](../src/WhateverXe/) |
| R16补丁顺序 | [patches/wex-0.8.2-r16/series](../patches/wex-0.8.2-r16/series) |
| 来源与重放结果 | [source-provenance.json](../metadata/source-provenance.json) |
| 公开WEX可执行SHA256 | `515f9399e72d7a761cd5bde32dfcb92d23be97e671f2d4ca5ec2ffa7db6a6d1a` |

当前树包括13路径生产补丁和11路径测试适配。补丁已在固定上游重放，公开二进制与本机可信读回一致；尚未以同一完整输入清单重建出相同二进制。

重放补丁时从固定上游开始，按 `series` 顺序应用。仓库的当前源码树已包含补丁。准备所需的 [Lilu](https://github.com/acidanthera/Lilu)、[MacKernelSDK](https://github.com/acidanthera/MacKernelSDK)及源码要求的工具链后运行：

```sh
cd src/WhateverXe
python3 tools/build.py
python3 tools/test.py
```

记录工具链、依赖和选项；新构建得到的Compat不可直接视为已记录的系统侧Compat。

本机改动涵盖A788门禁、R5／R6诊断、显示接管相关路径、媒体软件规避和背光算术。各项硬件验证范围不同；上游已有的[保留固件布线与延后激活](https://github.com/b00t0x/WhateverXe/commit/37580ea572c8858c3a584aea9a58e9c60f102ca9)不计作本机新增机制。

## 工具与独立贡献

| 内容 | 入口 | 验证范围 |
|---|---|---|
| 公开包检查 | [verify_package.py](../tools/verify_package.py) | 配置脱敏、当前／回退差异、USB配对及文件指纹 |
| USB只读采集 | [collect-usb-firmware](../tools/collect-usb-firmware/) | HS04／SS02与固件属性；旧HS02数据另列，离线解析／隐私测试已运行 |
| 基础Metal测试 | [metal-smoke](../src/metal-smoke/) | 历史七项作业源码，结果按会话记录 |
| 背光64位算术 | [backlight64](../contributions/backlight64/) | Linux／Clang x86_64执行旧／新23字节窗口：589,824组输入、1,769,589项检查 |
| AuxKC原生shell候选 | [auxkc-upstream](../contributions/auxkc-upstream/) | 30项shell／模拟kmutil测试；真实macOS缓存激活和回滚未验证 |
| AuxKC独立检查器 | [tools/auxkc](../tools/auxkc/) | Windows／Linux各32项模型测试，只生成和检查候选 |

背光host检查不等于macOS构建、hook可达性或全部面板场景通过。上游main缺少其R16依赖链，该贡献暂留自仓。

AuxKC候选已推到[自己的fork](https://github.com/gndb/WhateverXe-Graphics/tree/codex/auxkc-preserve-external-members)；上游限制PR创建权限，尚无上游PR编号，草稿与补丁保留在贡献目录。

## 提交与验证

修改后运行 `python3 tools/verify_package.py`，并运行涉及工具自己的离线测试。新增硬件结果应同时记录配置／二进制指纹、同一会话、输入规模和读回结果。历史缺失详细日志的计数不作为新跑结果。

从仓库根目录运行 `python3 tools/pack_latest.py --output ../R16-release` 可生成当前公开包。输出目录应在仓库外；包内文件有独立清单与校验值。

旧0.8.0源码、实验配置和原构建记录通过[历史索引](HISTORY.md)恢复；当前主分支集中维护0.8.2-R16。
