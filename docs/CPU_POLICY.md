# CPUFriend与EPP64政策

11月14日可用会话记录CPUFriend1.3.0和DataProvider1.0.1加载，条目限定Darwin25.0.0–25.99.99。配置意图是全局EPP64并保留原QoS；加载、注入意图、实际寄存器和性能收益分别判断。这里没有宣称睿频、续航或功耗获得测量改善。

当前Provider内嵌完整电源XML与频率向量，原数据块不在公开包。配置保留启用条目作为本机档案，使用者必须先生成自己的Provider并补齐文件；否则不能组成该配置的完整测试副本。

按[CPUFriend官方说明](https://github.com/acidanthera/CPUFriend/blob/master/Instructions.md)理解FrequencyVectors和完整电源plist格式，保留自己的原始数据，再应用经过理解的参数变化。官方工具可从本地完整修改plist生成Provider，例如在隔离工作目录运行：

```sh
./ResourceConverter.sh --kext /path/to/own-modified-power.plist
```

这条命令生成数据载体，不自动决定适合本机的EPP/QoS值。若选择停用CPUFriend与Provider两条配置，应记录为另一个配置，分别观察实际频率和负载，不沿用原基线的完整对应关系。
