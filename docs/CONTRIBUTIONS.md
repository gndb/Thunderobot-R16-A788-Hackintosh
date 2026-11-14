# 独立贡献与上游范围

## 背光64位算术

[contributions/backlight64](../contributions/backlight64/)保存从本机生产改动提取的算术窗口、来源对应和可运行host检查。测试header与生产源SHA一致；Linux/Clang x86_64实际执行旧/新23字节指令窗口，589,824组输入、1,769,589项检查通过，退出0。

这项检查不等于macOS构建、内核装载、hook可达性或所有面板硬件验收。该功能当前依赖R16的native-fallback/R5/R6可达链，上游main不具备这些前提，所以本次放在自仓，没有为了发PR而把缺失依赖的大量本机代码一并提交。

## AuxKC 既有外部成员

[AuxKC上游候选](../contributions/auxkc-upstream/)保存原生shell补丁、30项真实shell/模拟kmutil测试和准备好的草稿PR正文。独立审查后修正了未知行被忽略、数值相近版本误比较两处问题；最终候选已推到[自己的fork分支](https://github.com/gndb/WhateverXe-Graphics/tree/codex/auxkc-preserve-external-members)。真实macOS缓存激活、完整安装/卸载与回滚尚未验证。

实际创建PR请求被拒绝，仓库元数据确认上游采用`pull_request_creation_policy=collaborators_only`。因此本次没有上游PR编号，按本项目保留候选。后续获得协作者资格或上游开放后可使用已准备的补丁和正文。

[独立Python工具](../tools/auxkc/)仅生成和核对候选，不替换活动缓存；Windows与Linux各32项模型测试通过，不包含Apple载荷。

## 适合保留为问题案例的材料

冷启动/唤醒、Type-C负结果和用户态加载问题分别保留为[专题](issues/README.md)。现有证据不足以支持最小可验证修复的，不能用一次桌面成功替代因果或长期验收。上游已合并的固件布线/延后激活机制也不算本机原创。
