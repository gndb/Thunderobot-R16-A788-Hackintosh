# 双 GPU 基础 Metal 测试源码

这里保存2026-11-13本机七项作业对应的原始源码，文件哈希见../../metadata/dual-gpu-tests.json。它们针对Intel 8086:A788和NVIDIA 10DE:2C19选择设备，不是通用显卡基准。

在已装好图形栈、可以运行Metal的macOS上，使用Xcode Command Line Tools编译：

```sh
xcrun clang -fobjc-arc -fblocks dual-metal-smoke.m -framework Foundation -framework Metal -framework IOKit -o /tmp/r16-metal-smoke
xcrun clang -fobjc-arc -fblocks dual-triangle-smoke.m -framework Foundation -framework Metal -framework IOKit -o /tmp/r16-triangle-smoke
xcrun clang -fobjc-arc -fblocks dual-queue-smoke.m -framework Foundation -framework Metal -framework IOKit -o /tmp/r16-queue-smoke
```

分别运行七个作业：

```sh
/tmp/r16-metal-smoke --compute intel
/tmp/r16-metal-smoke --render intel
/tmp/r16-metal-smoke --compute nvidia
/tmp/r16-metal-smoke --render nvidia
/tmp/r16-triangle-smoke intel
/tmp/r16-triangle-smoke nvidia
/tmp/r16-queue-smoke
```

测试使用MSL2.3和小规模数据读回，不做性能、长稳、跨GPU资源共享或显示呈现验收。双队列先提交后等待不证明硬件执行时间重叠。应同时检查退出码、passed、超时和读回差异。

输出中包含动态registryID和servicePath，分享前需脱敏。不要直接把完整原始输出提交到公开仓库。
