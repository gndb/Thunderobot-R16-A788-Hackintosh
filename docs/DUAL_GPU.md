# 11月13日双GPU历史验收

2026-11-13 05:27（UTC）的同一macOS会话中，Intel A788驱动内屏，RTX5080 Laptop作为headless Metal设备工作。这里保留WEX0.8.0/NVIDIA2.7.2的历史验证，不将结果升级为0.8.2/NV3.0验收；新版范围见[会话矩阵](issues/dual-gpu-sessions.md)。

## 历史配置档

| 档案 | 位置 | 范围 |
|---|---|---|
| 旧公开根快照 | [historical-20261113/EFI](../profiles/historical-20261113/EFI/) | 05:27后同显卡栈快照；去掉-v、有线改3.0.4，新有线只有引导注入记录 |
| 精确七项双GPU档 | [dual-gpu-verified-0527](../profiles/dual-gpu-verified-0527/EFI/OC/config.plist) | 对应七项作业会话，保留-v、有线2.4.2 |
| 核显独立历史档 | [igpu-only-20261113](../profiles/igpu-only-20261113/EFI/OC/config.plist) | 早前核显路线，保留-nvoff |

这些历史profile现在保留自己的旧公开载荷，仍须按各自依赖表补齐，不再共用已经更新为0.8.2的根EFI。旧系统侧Intel配套和NV2.7.2也不能被新依赖版本默默替换。

## 原同会话作业

| 作业 | Intel A788 | RTX5080 Laptop |
|---|---|---|
| 整数计算并读回256元素 | 通过 | 通过 |
| 清屏并读回16×16纹理 | 通过 | 通过 |
| vertex/fragment三角形及16×16像素读回 | 通过 | 通过 |
| 同一进程向两卡各自队列提交，再分别等待 | 通过，末元素1037 | 通过，末元素2037 |

三项分别运行两卡，加一项共同进程双队列，共七个案例；记录为零读回差异和零超时。使用MSL2.3，双队列各自独立资源，没有跨GPU共享，也没有测量执行是否重叠。

脱敏结果在[dual-gpu-tests.json](../metadata/dual-gpu-tests.json)，源码在[metal-smoke](../src/metal-smoke/)。测试源码运行时可能输出设备registryID和servicePath，自行分享结果需另作脱敏。

## 未覆盖

基础离屏测试不证明跨GPU画面转交、自动MUX、性能相加、RTX直接驱动内屏、完整视频编解码、外屏或长期负载。冷启动、熄屏和睡眠恢复问题仍保留，见[STATUS](STATUS.md)。
