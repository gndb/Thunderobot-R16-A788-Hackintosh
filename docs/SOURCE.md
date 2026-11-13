# 自定义 WhateverXe 源码与构建来源

本仓库保存的是雷神 R16 / Intel `8086:A788` 的本机适配快照。它以 WhateverXe 0.8.0 为基础，并包含本机显示、加速器诊断、首次显示接管重试、媒体能力规避及背光算术修正。它不是 WhateverXe 上游发布版，也不能把本机成功推广到其他 A788 笔记本。

## 与成功载荷的对应关系

| 项目 | 值 |
|---|---|
| 构建产品 | WhateverXe.kext，x86_64 RELEASE，版本字段 0.8.0 |
| 可执行文件 SHA-256 | `7d7ee576fe84cc47919060a454d1b50bb718f54ee7b1872fb53fc20d2af2316a` |
| Mach-O 构建 UUID | `1C8BA045-8284-362F-9D61-3459AE2801A1`（构建标识，不是电脑的 SystemUUID） |
| 原始基底 | [b00t0x/WhateverXe，db438fdf4d5fe903f5dfbc65537ed3884e2ea980](https://github.com/b00t0x/WhateverXe/commit/db438fdf4d5fe903f5dfbc65537ed3884e2ea980) |
| HX 参考 | [rodgod-rr/WhateverXe，86693d3ea72541b5c6bf4a3e43844cca4b5c14ad](https://github.com/rodgod-rr/WhateverXe/commit/86693d3ea72541b5c6bf4a3e43844cca4b5c14ad) |
| 时钟恢复参考 | [rodgod-rr/WhateverXe，44b9aacde6bb569fcd71fe8e3db53510db8fa41b](https://github.com/rodgod-rr/WhateverXe/commit/44b9aacde6bb569fcd71fe8e3db53510db8fa41b) |

这些参考提交只说明采用过的机制来源，不表示整份 fork 原样移植、原作者为本机背书，或每项修改分别完成独立硬件验收。应保留各文件已有的著作权、SPDX 与来源注释；WhateverXe 根目录的 BSD-3-Clause 许可同样保留。AppleIntelTGLCompat 个别文件另有 BSD-2-Clause SPDX，不能用仓库总许可覆盖它。

发布源码对应最终背光 64 位算术候选的冻结输入。已将同次构建清单里的 151 个本地输入逐个比对：其中 150 个属于 WEX，另 1 个是同次构建的 Compat 入口。外部 Lilu 的 `plugin_start.cpp` 另列为 WEX 构建依赖。WEX 的 150 个本地输入均与上述二进制的已保存构建清单一致。此核对证明源码输入和已保存构建清单一致，不等于本次重新编译复现出逐字节相同的二进制。

## 修改层次

1. 上游 0.8.0 与经选择的 HX/VBT/时钟/面板初始化参考。
2. R16 的严格设备和原生调用目标门禁、R5 输出策略、R6 加速器 hook 次序及持久诊断。
3. R7 输出诊断、R9 有界的一次显示电源管理恢复尝试。
4. `-wex-r16-va-software` 的媒体能力规避，承认部分视频处理走软件路径。
5. `-wex-r16-backlight64`：保留原生控制流程，在经签名确认的 23 字节算术窗口修正 PWM 乘法溢出；它相对父版本只改 `kern_xe.cpp`、`kern_xe.hpp`，新增 `kern_r16_backlight64.hpp`。

本快照不包含后来独立的 R10/R11 熄屏恢复试验，也不包含 240 Hz 实验代码。本次配置更新已经加入并实测WEX＋NVIDIA2.7.2 headless基础共存，WEX二进制和编译输入没有变化；原核显独立档案仍停用NVIDIA。

## 源码目录与构建

源码快照提供 `WhateverXe/`、`AppleIntelTGLCompat/`、`tests/`、`tools/`。保留上游 `LICENSE.txt` 后，它可以作为命令行构建用源码；它不是带完整文档和 Git 历史的上游仓库克隆。

使用源码内的 `tools/build.py`，另行准备对应的 [MacKernelSDK](https://github.com/acidanthera/MacKernelSDK) 和 [Lilu 开发包](https://github.com/acidanthera/Lilu)：

```sh
python3 tools/build.py --release --sdk /path/to/MacKernelSDK --lilu /path/to/Lilu.kext --output build
```

当前保存载荷来自 Ubuntu/Clang 14.0.0 和 Apple ld64 956.6 的交叉构建；上述原生命令行入口使用 macOS 的 `xcrun` 工具链。构建入口、依赖与链接环境都应核对，不承诺不同工具链生成相同 SHA-256。

构建脚本也会生成 AppleIntelTGLCompat；该产物不是本次成功 EFI 的部署对象。请保留已验证的 macOS 侧 Compat/Graphics 配套，不要因为同次构建产生了一个新 Compat 就自动替换。Apple donor 驱动与系统组件不属于本仓库可再分发的自定义源码。

## 公开与私有信息

设备 ID、A788 门禁、寄存器偏移、驱动字节签名、构建 UUID 和通用 OpenCore 诊断命名空间可用于解释适配。源码扫描未发现本机序列号、MLB、MAC 地址或 SystemUUID。`tools/package.py` 中的 `/Users/`、`/home/` 字面值用于检查构建路径泄漏，不是个人路径。

完整运行报告、IORegistry/NVRAM 原始转储、卷 UUID、用户目录、旧 EFI 备份和内部部署回执不随源码公开。

公开整理只调整了一个非编译输入的辅助测试：`tests/small_gt_urb-retain-review.py` 改用隔离临时目录，移除本机固定输出位置。同次构建的151个本地输入和发布WEX二进制未改变；修改前后哈希记录在源码清单。
