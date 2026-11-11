# 行动与证据

日期：2026-11-12（Asia/Shanghai）。日志中时间戳使用 UTC；对应本地同一天。以下是实际行动，不以计划内容替代执行结果。

| 顺序 | 行动 | 观察/证据 |
|---|---|---|
| 01 | 读取当前源码、计划、依赖、解释器和 Git 状态，固定起点 | HEAD 52c4972；`evidence/baseline.json`；执行前已存在其他 task 的改动 |
| 02 | 核对最新稳定版本及 Requires-Dist | `pypi-candidates.json`；收尾再核对 `latest-version-recheck.json` |
| 03 | 迁移特性基线并创建步骤目录、run-01 | 所有 S01 细节集中到本目录；根入口按用户确认渐进式披露 |
| 04 | 只修正批准的其他 task 链接 | `approved-link-repairs.json`、`other-task-scope-check.json`；13 个其他 task 文件与初始字节核对通过 |
| 05 | 求解旧/新依赖，创建三个独立环境及 8 份锁 | 旧 graph 原组冲突；LangServe/MCP SSE 冲突隔离；安装日志、`environment-verification.json` |
| 06 | 接入 create_agent、middleware、结构化输出、context 和内容块 | `lib_graph.runtime`；新版特性行为测试；工具循环由框架执行 |
| 07 | 迁移内置 MCP、FastMCP/MCP 2、HTTP/stdio 与资源 | `agentmcp`、MCP manager、数学/天气服务；嵌套 schema 保留；新版等待输入协议 |
| 08 | 首轮反馈修复 | 9 通过/3 失败的历史日志保留；修正 async v3 output()、stdio 显式 env、InputRequiredResult；后续最终结果已覆盖这些失败 |
| 09 | 旧流程回归并修复必要阻塞 | Manus 状态漏声明、泛化 src 导入、讨论循环导入、日志目录；editable 包在仓库外导入通过 |
| 10 | LangServe/UI/RAG 回归 | 路由/schema/invoke/stream；PDF、Word、文本、FAISS、旧检索链；SQL 只读负例；调试日志不输出凭据 |
| 11 | 按用户指定切换 DeepSeek Flash，纠正私密配置落点 | 新凭据仅在 `.env.local`；受控 `.env` 恢复原字节；主要文本入口环境配置生效 |
| 12 | 真实 DeepSeek 冒烟 | `live-model.json`：文本、流式、ToolStrategy 3 项通过；此前其他模型回执单独保留为历史，不作当前模型证明 |
| 13 | 真实 DeepSeek → HTTP MCP 工具 → 最终回答 | `live-mcp-model.json`：calculator 返回 84，最终答案核对通过，临时服务已停止 |
| 14 | 最终回归 | Agent/MCP/旧流程 23、LangServe 3、UI/RAG 5，共 31 项通过；三份最终 XML/log |
| 15 | 依赖、锁、API 与源码回读 | 三环境 pip check；Poetry check；两个 uv lock --check；10 个 API 符号可用；静态检查和精确写集见最终回执 |
| 16 | 回滚副本演练、文档收尾 | 228 个归档文件恢复原字节通过；两个解释器文件另存；不覆盖实际工作区、不声称旧依赖重建通过 |

## 证据读法

最终行为结果使用 `agent-tests.xml`、`langserve-tests.xml`、`ui-rag-tests.xml`、`live-model.json`、`live-mcp-model.json`。`native-mcp-first-attempt.log`、`native-mcp-tests.log`、`existing-workflow-tests.log` 是修复前历史，不能当成最终状态。安装日志、锁检查和 API 可用性是不同证明层级，不能代替真实行为或生产验收。

执行命令与环境重建方法见 [安装使用指南](../upgrade-guide.md)。本轮没有启动 S02，没有 commit、push、部署或对外发消息。

补充核对：为旧 SDK DeepSeek 工具循环显式关闭思考模式，Manus 的实际 SDK 请求体已由 MockTransport 验证；新增 PDF fixture 验证读取内容及页码来源，修正 fixture 的页面对象与来源断言后通过。
