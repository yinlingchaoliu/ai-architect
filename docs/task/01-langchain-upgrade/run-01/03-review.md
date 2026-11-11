# 复盘：兼容验证与交付结论

日期：2026-11-12。结论：**S01 升级及所定义兼容切片完成，自审通过；未执行 S02。** 这不表示新多智能体平台已经实现，也不表示全仓所有历史脚本、所有外部服务和生产环境均已验证。

## 1. 候选与实装

采用 LangChain **1.5.0**、langchain-core **1.8.0**、LangGraph **1.2.20**、langchain-openai **1.7.4**、OpenAI SDK **3.49.0**、Pydantic **2.14.3**。Agent/MCP 使用 FastMCP **4.1.8**、MCP SDK **2.3.0**；Python **3.12.15**。收尾实时复核主要包仍为 PyPI 最新未撤回稳定版本，见 [版本复核](evidence/latest-version-recheck.json)。

三个独立环境的依赖检查均通过，分别记录 104、61、136 个已安装包；其中含本地 editable 工程包。Agent/MCP 与 LangServe 的 SSE extra 存在硬冲突，采用进程/环境隔离，未降低新 LangChain/core/graph/provider。最终选择、安装步骤、8 份锁的 hash 见 [指南](../upgrade-guide.md) 和 [环境回执](evidence/environment-verification.json)。Poetry 与两个 MCP uv 锁检查通过；Poetry 安装、两个独立 uv 环境安装没有另行执行。

## 2. 确定性回归结果

| 验证组 | 结果 | 实际覆盖 |
|---|---|---|
| Agent/MCP/旧流程 | **23 passed** | create_agent 工具多轮、非法结构化结果拒绝、模型调用上限、context、内容块、同步/异步 v3；中断恢复与副作用；真实 HTTP/stdio MCP、资源、elicitation、嵌套 schema、原客户端；会议/Manus/旅行/讨论流程、同步异步 SDK 和配置覆盖 |
| LangServe | **3 passed** | 4 个既有路由、health、OpenAPI/input schema、invoke、SSE delta 组装、prompt、GET/POST 样例 |
| UI/RAG | **5 passed** | 实际 PDF/Word/文本读取、splitter、FAISS、旧检索链来源、web_search 新导入、Chat 模型 SQL 结果、SQLite 拒绝 DELETE、Embedding 形状、请求 SDK 模型配置与密钥日志负例、根入口导入 |
| 合计 | **31 passed** | 限定 S01 回归集合；模型/Embedding 用 fake 或 MockTransport，MCP 协议和数据库为实际本地运行 |

最终原始证据：[Agent XML](evidence/agent-tests.xml)、[Agent 日志](evidence/agent-tests.log)、[LangServe XML](evidence/langserve-tests.xml)、[LangServe 日志](evidence/langserve-tests.log)、[UI/RAG XML](evidence/ui-rag-tests.xml)、[UI/RAG 日志](evidence/ui-rag-tests.log)。另有 [仓库外导入检查](evidence/package-imports.json) 和 [API 可用性](evidence/api-availability.json)。API 可用性不能替代行为验证。

## 3. 用户指定模型的真实验证

模型 **deepseek-flash**，provider **api.deepseek.com**。通过 OpenAI 兼容 Chat Completions，明确非思考模式，超时 30 秒、零自动重试、每次最大 128 输出 tokens。未记录原始密钥、完整鉴权请求或原始 provider 错误。

| 真实检查 | 结果 | 证据 |
|---|---|---|
| 文本 | 通过，核对 S01_OK | [live-model.json](evidence/live-model.json) |
| 流式文本 | 通过，核对 STREAM_OK | 同上 |
| create_agent + ToolStrategy | 通过，Pydantic marker 为 STRUCTURED_OK | 同上 |
| 真实模型 → create_agent → HTTP MCP → 模型答复 | 通过；实际 calculator 结果与最终答复均为 84；临时子进程已停止 | [live-mcp-model.json](evidence/live-mcp-model.json) |

回执保留已返回的 usage_metadata；流式 usage 未收集齐，不能把可见记录之和称作全轮计费总量，也未计算价格、吞吐或业务质量。该冒烟证明本轮 SDK/API 与此 provider 的有限兼容，不证明其他模型、Responses API、思考模式、严格 provider JSON Schema、真实天气或真实 Embedding 可用。切换前其他 provider 的回执仅留作历史。

## 4. 新能力采用程度

| 能力 | S01 结果 | 边界 |
|---|---|---|
| create_agent / middleware | 实际代码接入，动态 prompt、调用上限及工具循环验证 | 平台累计预算与统一身份尚未接入 |
| ToolStrategy / structured_response | 本地行为及真实 DeepSeek 验证 | ProviderStrategy 仅 API 可用，不声称 provider 严格输出通过 |
| content_blocks / Runtime / ToolRuntime | 本地行为通过，response.text 兼容内容块 | 不能由 runtime.context 自动产生平台授权 |
| v3 streaming | sync/async 增量和最终结果验证 | 实际实现标 experimental；未落平台持久事件 |
| 内置 MCPAdapter | 真实本地 HTTP/stdio、资源、等待续答、关闭通过；真实模型 HTTP 链路通过 | beta；多服务平台治理、sampling/roots 完整行为未验收 |
| StateGraph / checkpoint / interrupt | 旧图回归、内存暂停恢复、恢复前无副作用/恢复后一次执行通过 | 无 PostgreSQL、跨进程重启、跨租约和外部副作用对账证明 |
| ModelRouterMiddleware | 符号可用 | 路由/auto mode 行为待既定 S03/S06；本轮静态指定 DeepSeek |

## 5. 修复与限制

必要修复包括 Manus 未声明状态导致循环、多个 src 包冲突、讨论系统循环导入/日志目录、OpenAI SDK 同步异步消费、MCP schema 与等待输入、旧 LangChain 导入、SQL Chat 模型和只读连接。保留现有会议/Manus/旅行业务策略，未将它们改造成四种平台协作策略。

仍存在上游警告：MCPAdapter beta、v3 experimental、LangServe 使用 Pydantic 旧实例字段访问；community/experimental 逐步停止维护、PyPDF2 弃用以及旧 Poetry 元数据警告。已保留日志，兼容组隔离；本轮不修改 site-packages。pytest-asyncio 默认 fixture loop scope 也有弃用提示，不影响本轮结果。

未运行：Streamlit 浏览器操作、真实天气 API、真实 Embedding、语音/图像专用 API、LlamaIndex 独立旧栈、所有历史 integration/performance 脚本、吞吐压力、生产部署、数据库持久恢复。业务原有“失败仍完成”等语义与跨 Run 累计预算不由本轮兼容测试证明，仍按既定后续任务处理。

## 6. 写集、回滚与下一步

最终写集与 hash 见 `evidence/write-set.json`，静态和文档核对见 `evidence/final-verification.json`。其他 task 的 13 份文档按起始工作区核对，只含用户批准的链接替换，既有内容保留；根总任务状态文件是原有计划快照，本轮没有越界改写它们。

[回滚副本演练](evidence/rollback-check.json) 验证 228 个归档文件字节恢复。没有执行真实工作区回滚或旧环境安装；旧会议精确 requirements 本身不可求解。具体恢复步骤和兼容例外见 [回滚说明](../rollback.md)。

审阅方式为 **self_review**，没有独立审阅或用户验收签认。S01 交付可供下一步采用；本轮不自动开始 S02，不改写其方案。如需调整其他 task，先展示具体修改并取得用户确认。
