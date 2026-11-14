# 11月14日可用实验基线

对应本机15:49成功会话，公开EFI为脱敏的部分载荷。WEX0.8.2-R16；系统侧Graphics0.4.4/Compat0.8.1/NV3.0须另行安装。

证据范围：正常桌面、2560×1600/60Hz、连续亮度、Intel1024元素计算/回读0错；NV3.0四模块加载，headless。本次没有重新完成七项双GPU作业，也未完成重复冷启动、熄屏唤醒或长期稳定性验收。

本档没有后来加入的666字节USB固件诊断表。当前Type-C/PD仍有问题；高刷关闭。不要将[USB实验档](../experimental-usb-firmware-20261114/README.md)的部署当成这个成功会话已经测过的内容。

使用前按[INSTALL](../../docs/INSTALL.md)填自己的SMBIOS、补齐所有启用依赖，并生成自己的CPUFriendDataProvider。公开配置不是可直接覆盖启动盘的完整EFI。
