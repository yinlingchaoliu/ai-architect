# 行动：本轮实际操作

日期：2026-11-12（Asia/Shanghai）。这是研究记录，不是实现进度。

| 顺序 | 实际行动 | 输出/观察 |
|---|---|---|
| 01 | 回读用户约束、当前Git状态与参考路径 | 正式llm目录不改；仅本run-01写入；项目arch未作为依赖 |
| 02 | 获取参考HEAD/状态、扫描五包目录和主调用符号 | 参考HEAD 47f9438，工作区干净；不是按README代替源码 |
| 03 | 定向读取Runtime、types、message、prepareCall、注册/替换和assembler | 稳定seam、注册快照、replay边界和单次handle等事实 |
| 04 | 读取DeepSeek/Pi-ai两个适配器、serializer、SSE/translate/replay | 一次配置捕获、consumer取消、terminal、cache usage和未知扩展等机制 |
| 05 | 读取retry/token-meter实现及关键测试用例 | 重试先记日志、always模式、相邻step投影条件；测试只读未执行 |
| 06 | 回读现有ModelProvider草案与本项目源码 | 识别原生LangChain与自建raw协议重复的潜在成本；未改正式草案 |
| 07 | 读取S01环境实际安装源码与官方文档 | LC1.5.0/core1.8.0/provider1.7.4/LG1.2.20；核对async fallback、middleware顺序和输出处理 |
| 08 | 建立本轮输入和16个受保护文件hash | evidence/baseline.json，包含23个定向参考源/测试指纹；不读取.env |
| 09 | 运行离线LangChain机制探针，退出0 | native/sync-only线程区别、chunk usage相加、schema错误前usage已可见；补充验证AsyncCallback读取attempt scope及finally reset；network_calls=0 |
| 10 | 写分析、思考、优化候选、复盘和反思 | 全在run-01；没有platform实现、依赖变更或真实模型请求 |
| 11 | 文档链接、图源、输入/保护文件与候选写集回读 | 结果见evidence/document-check.json；不据此声称性能/计费系统通过 |

可复现离线命令：

```bash
/Users/chentong/AI/PatientCare/.venvs/ai-architect-s01/bin/python docs/task/02-platform-contracts-and-skeleton/run-01/evidence/langchain-mechanism-probe.py
```

探针只用Fake模型与Python本地线程/框架机制，不联网、不需要provider密钥。参考TypeScript测试、真实模型、真实多租户、压测和生产部署均未执行。
