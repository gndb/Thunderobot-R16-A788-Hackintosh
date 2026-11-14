# BetterDisplay 5.2.1 UD2崩溃

状态：应用级崩溃，需补最小复现与符号/断言信息。

11月14日15:49图形会话附近，BetterDisplay5.2.1出现SIGILL / EXC_BAD_INSTRUCTION；故障位置在应用自身，opcode为UD2，应用启动后约4秒发生。已有信息支持定位到应用故障，尚不足判断具体断言或驱动因果。

上游应用报告应包含：应用版本、系统build、触发步骤、是否空白配置也复现、image-relative偏移及最短脱敏栈。原IPS含个人路径和会话信息，不直接上传。

不能把UD2直接解释为CPU不支持AVX，也不能凭同时出现图形fence/沙盒日志就确认核显导致。WebKit库映射拒绝[单独记录](webkit-sandbox.md)。
