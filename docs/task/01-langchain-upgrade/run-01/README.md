# S01 / run-01

日期：2026-11-12（Asia/Shanghai）。状态：**completed，self_review**。目标：升级最新稳定 LangChain/LangGraph、采用新能力，完成本轮定义的兼容验证并记录结果。

实际结果：LangChain 1.5.0 / LangGraph 1.2.20 / Python 3.12.15；三个环境依赖检查通过，31 项回归通过；用户指定 deepseek-flash 的文本、流式、ToolStrategy 和真实 HTTP MCP 往返共 4 项检查通过。

- [思考：判断依据与取舍](01-thinking.md)
- [行动与证据](02-actions.md)
- [复盘与验证结论](03-review.md)
- [反思与后续](04-reflection.md)
- [安装和使用](../upgrade-guide.md)
- [回滚说明](../rollback.md)
- [初始基线](evidence/baseline.json)
- [最终环境和锁 hash](evidence/environment-verification.json)
- [最终写集](evidence/write-set.json)
- [最终静态和文档检查](evidence/final-verification.json)

记录可观察的判断依据、决定、行动和结果，不记录模型隐含推理。密钥和完整环境变量不进入证据。历史失败日志保留，最终结果以上述复盘所指回执为准。S02 未开始，生产、持久恢复和未覆盖的外部服务均未宣称通过。
