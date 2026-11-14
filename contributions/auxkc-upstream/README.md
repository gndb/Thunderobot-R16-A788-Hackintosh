# AuxKC 既有外部成员保留候选

候选面向 [WhateverXe-Graphics](https://github.com/b00t0x/WhateverXe-Graphics) 安装器。旧辅助内核集合可能包含 `/Library/Extensions` 之外的已注册成员；仅重新枚举该目录会遗漏这些输入。

本目录保存原生 shell 修复补丁、测试及草稿 PR 正文。补丁在重建时携带既有外部成员，并在替换前检查候选集合中的精确 bundle ID 和版本；未知解析格式拒绝继续。既有安装器的缓存替换逻辑仍然存在，因此此补丁不能用作已通过真实 macOS 验收的安装包。

- 上游固定基底：`61c7cddda38d6a5d0057a01f402aab6efb612e13`。
- 候选提交：[`a79eae9`](https://github.com/gndb/WhateverXe-Graphics/commit/a79eae9f2eb87ea162e648fa3c99884ddb4bea57)。
- 补丁：`preserve-external-auxkc.patch`，在固定基底执行 `git apply --check` 后应用。
- 测试入口：应用补丁后执行 `python3 tools/test_auxkc.py`。
- 结果：Linux/WSL 真正执行 shell helper，模拟 kmutil，30 项通过；未运行真实 macOS kmutil、完整包安装/卸载、缓存激活或回滚。

**未创建上游 PR。** 2026-11-14 实际创建请求被拒绝；随后读取仓库元数据确认 `pull_request_creation_policy=collaborators_only`，当前账号不是协作者。候选已推到自己的 fork，补丁和[准备好的 PR 正文](PR_BODY.md)保存在本项目，不绕过该仓库规则，也不冒称已提交。

可独立使用的 [Python 候选检查工具](../../tools/auxkc/)只有计划和生成候选功能，不替换活动缓存；它是另一份实现，32 项模型测试通过。两种实现的测试结果不可互相当作真实 macOS 证明。

上游工具的 BSD-2-Clause 许可保存在 `LICENSE.txt`；不包含 Apple bundle 或内核缓存。
