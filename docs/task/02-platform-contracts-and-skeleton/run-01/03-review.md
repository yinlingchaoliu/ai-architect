# 复盘：结论与证明范围

日期：2026-11-12。状态：本轮研究/方案比较完成，候选待用户确认。review_mode=self_review，未做独立评审或用户验收。

## 1. 对三项用户要求的回应

1. 已读取deepseek-harness/packages/llm五个包的关键实现与测试：稳定seam、配置/注册快照、prepareCall、native/generic双适配、回放、流式取消、重试和计量投影。事实定位见 [分析](00-analysis.md)，源码不是仅凭包名/README推断。
2. 已给出LangChain优先的 [完整优化候选](05-langchain-optimization.md)：native backend与共用治理、PreparedInvocation、模型/连接复用、异步与双路径、callback collector、usage语义、并发扩展和验证计划。
3. 正式llm目录保持原字节；所有新记录在本run-01。是否将候选合入正式方案由用户确认，其他task也未修改。

## 2. 已运行的三个机制观察

[实际回执](evidence/langchain-mechanism-results.json) 与 [脚本](evidence/langchain-mechanism-probe.py) 绑定当前安装版本及6份framework文件hash。

| 观察 | 实际结果 | 能证明与不能证明 |
|---|---|---|
| async线程路径 | sync-only的ainvoke/astream在executor线程；native实现留在event-loop线程 | 能暴露默认fallback；不能证明真实provider吞吐、零阻塞或无其他线程 |
| usage chunk合并 | 人工构造的累计total快照11、14被框架相加成25 | 说明自定义映射不能把累计快照当delta；不是LangChain原生provider重复计费的证明 |
| middleware与schema失败 | outer→inner→provider on_llm_end→StructuredOutputValidationError，usage total=5已可见 | 说明handler错误不等于模型未完成、不能只按Agent成功取usage；异步回调读到attempt scope且错误后reset；不是并发隔离或持久collector/账本验证 |

三个观察均通过，脚本退出0，network_calls=0。没有把三个机制观察称成完整平台测试套件。

## 3. 对参考源码的评价

它的突出价值是职责、生命周期和协议保真，不是“代码少所以并发高”。可以借鉴prepareCall与新旧快照隔离，但其同步注册原子性和进程内一次handle不是跨进程幂等。token-meter是会话投影和上下文估计，不是货币预算账本；其相邻step去重条件不能直接推广到分布式乱序usage。

一些行为应在平台边界收紧：always retry、缺finish的assembler默认stop、非法历史tool JSON回退{}、未报告cache展示为0、until-DONE才发usage。它们的使用上下文各有约束，不应脱离上游检查宣称整个参考项目有相应故障；更不能直接照搬为生产平台合同。

## 4. 对前轮方案的修正

前轮保持厂商隔离、预算权威和错误/费用分离的目标应保留；默认raw Driver+Bridge的路径需要重新评估。框架已选LangChain时，生态复用应进入主执行路径，自有抽象集中在可信context、生命周期、治理和对外合同。新候选还未实测，不能宣称已提升某个百分比或一定优于所有通用Bridge实现。

## 5. 未验证与交付

未执行参考TypeScript测试、真实DeepSeek/其他厂商、负载/公平性实验、PG/Redis账务/恢复、取消远端推理、生产部署和Mermaid图片渲染。新增候选的schema、代码骨架和middleware组合均未实现。

文件/链接/图源和受保护输入核对见 [document-check.json](evidence/document-check.json)。这只是结构与输入保留验证；语义审阅为本轮自审。下一消费者是用户方案评审，确认前不合入../llm正式文档。
