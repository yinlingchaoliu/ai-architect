# S01 安装、配置与使用指南

日期：2026-11-12。对应 [run-01 验证结论](run-01/03-review.md)。本轮实装环境为 macOS、Python **3.12.15**、uv **0.12.24**。核心包按当日 PyPI 未撤回稳定版核验，并在三个独立环境中实际安装。

## 1. 最终依赖与环境边界

| 组件 | 实装版本 | 范围 |
|---|---|---|
| langchain | 1.5.0 | 三个环境一致 |
| langchain-core | 1.8.0 | 三个环境一致 |
| langgraph | 1.2.20 | 三个环境一致 |
| langchain-openai | 1.7.4 | 三个环境一致 |
| openai | 3.49.0 | 三个环境一致；同步/异步 SDK 均有回归 |
| pydantic | 2.14.3 | 三个环境一致 |
| fastmcp / mcp | 4.1.8 / 2.3.0 | Agent/MCP 和 UI 可选组；服务测试使用 Agent 环境 |
| langserve / fastapi | 0.3.3 / 0.162.4 | LangServe 环境 |
| classic / community / experimental | 1.0.8 / 0.4.2 / 0.4.2 | UI/RAG 遗留消费组 |

LangServe 的 server extra 依赖 `sse-starlette<2`，MCP 2.3.0 依赖 `sse-starlette>=3`。因此保留 **Agent/MCP、LangServe、UI/RAG 三个环境**，LangServe 单独运行；没有强装冲突版本。三个环境共享相同的新 LangChain/core/LangGraph/provider 版本。UI/RAG 组包含 Agent/MCP 基础组，但不安装 LangServe server extra。

本机路径分别为 `/Users/chentong/AI/PatientCare/.venvs/ai-architect-s01`、`ai-architect-s01-server`、`ai-architect-s01-ui`。完整包清单、三次依赖检查和锁文件 SHA-256 见 [environment-verification.json](run-01/evidence/environment-verification.json)。最新发布复核见 [latest-version-recheck.json](run-01/evidence/latest-version-recheck.json)。

## 2. 从锁文件复现

在仓库根目录执行，环境路径可调整。`pip sync` 用于新建的独立环境；安装本地 editable 包放在 sync 之后。

```bash
S01_AGENT_VENV=/Users/chentong/AI/PatientCare/.venvs/ai-architect-s01
S01_SERVER_VENV=/Users/chentong/AI/PatientCare/.venvs/ai-architect-s01-server
S01_UI_VENV=/Users/chentong/AI/PatientCare/.venvs/ai-architect-s01-ui

uv venv --python 3.12.15 "$S01_AGENT_VENV"
uv pip sync --python "$S01_AGENT_VENV/bin/python" --require-hashes requirements/s01-dev.lock
uv pip install --python "$S01_AGENT_VENV/bin/python" --no-deps -e ./lib_graph -e ./agent_muti -e ./agent_muti_discussion -e ./manus -e ./mcp_client_manager

uv venv --python 3.12.15 "$S01_SERVER_VENV"
uv pip sync --python "$S01_SERVER_VENV/bin/python" --require-hashes requirements/langserve.lock
uv pip install --python "$S01_SERVER_VENV/bin/python" --no-deps -e ./lib_graph

uv venv --python 3.12.15 "$S01_UI_VENV"
uv pip sync --python "$S01_UI_VENV/bin/python" --require-hashes requirements/ui-rag-dev.lock
uv pip install --python "$S01_UI_VENV/bin/python" --no-deps -e ./lib_request

uv pip check --python "$S01_AGENT_VENV/bin/python"
uv pip check --python "$S01_SERVER_VENV/bin/python"
uv pip check --python "$S01_UI_VENV/bin/python"
```

运行依赖和开发依赖分别锁定：`agent-runtime.lock` / `s01-dev.lock`，`ui-rag.lock` / `ui-rag-dev.lock`。根 requirements 与图、Manus、MCP 客户端等子项目入口指向同一组锁。约束源在 `requirements/constraints-langchain.txt`，可使用 `uv pip compile --python /opt/homebrew/bin/python3.12 --generate-hashes requirements/s01-dev.in -o requirements/s01-dev.lock` 重新求解；更新锁后必须重新验证，不能直接当作本轮已验证候选。

`server/poetry.lock` 已重新生成，`poetry check --lock` 通过；本轮应用实测使用 `requirements/langserve.lock` 安装，**没有额外宣称 Poetry 完整安装验证**。两个 MCP 子项目的 uv.lock 已更新，`uv lock --check --project …` 通过，`.python-version` 对齐 3.12.15；本轮协议实测使用 Agent 环境，未另外安装两个 uv 项目的独立环境。

## 3. DeepSeek Flash 本地配置

用户指定的模型为 **deepseek-flash**。项目已有受 Git 跟踪的 `.env`，本轮保留其原字节，新凭据写入被忽略的 `.env.local`（权限 0600）。主要文本入口优先读取 `.env.local`，进程中显式环境变量优先级更高；模型使用 `OPENAI_MODEL`，讨论系统兼容 `MODEL_NAME`。

本地文件的配置形状如下；实际密钥不写入本文、测试记录或 Git 差异：

```dotenv
OPENAI_BASE_URL=https://api.deepseek.com
OPENAI_MODEL=deepseek-flash
OPENAI_API_KEY=<仅在本地填写>
MODEL_NAME=deepseek-flash
```

DeepSeek 支持 OpenAI 兼容格式。此次真实验证使用 **Chat Completions、非思考模式、最多 128 输出 tokens/次、零自动重试**，通过 `extra_body={"thinking":{"type":"disabled"}}` 明确选择该模式。Manus、旅行、讨论和 MCP router 的旧 SDK 路径也为 DeepSeek 显式关闭思考模式，避免旧工具循环丢弃 reasoning_content 后触发协议错误。结构化输出使用 `ToolStrategy`，由 Pydantic 验证；未将其说成 provider 原生严格 JSON Schema 验证。[官方接入说明](https://api-docs.deepseek.com/)、[工具调用](https://api-docs.deepseek.com/guides/tool_calls/)、[思考模式限制](https://api-docs.deepseek.com/guides/thinking_mode/)

主要 Agent、会议图、LangServe、Web 搜索/PDF 问答、CSV/SQL 和请求 SDK 的文本模型改为读取环境配置；Manus 在读取 TOML 后应用显式环境覆盖，避免旧 GPT 配置继续生效。绘图、语音、Embedding 等专用模型仍是独立能力，不能把 DeepSeek 文本调用通过当作它们可用的证据。真实 Embedding provider 尚未验证；运行 RAG 前须配置可用的 Embedding 服务，不应将 DeepSeek 文本端点直接当作 Embedding 端点。UI 手动选择其他模型属于用户显式配置，不在本轮真实模型验收范围。

## 4. 新 API 与入口

- `lib_graph.runtime.build_agent` 使用框架 `create_agent`，默认接入 `ModelCallLimitMiddleware`，支持 context、结构化输出、checkpoint/store 注入，保留框架原生事件 API；不自建工具执行循环。
- `lib_graph.langgraph_hello` 是有界运行的示例，导入不会发起模型调用；天气工具明确标注演示数据。
- `agentmcp.agentmcp.run_query` 使用内置 `langchain.mcp.MCPAdapter` 的上下文发现和调用工具，退出时关闭连接。默认天气端点为 `http://127.0.0.1:8000/mcp`。
- MCP 数学/天气服务默认 Streamable HTTP `/mcp`，端口分别 8001/8000；`MCP_TRANSPORT=stdio` 显式选择子进程协议。资源仍经 FastMCP Client 使用；没有删除资源接口。
- 保留现有自定义 StateGraph 会议和 Manus 流程；修复新版图状态中未声明字段被丢弃的问题。旧流程的业务调度重构仍由后续 task 负责。
- WebUI/CSV 明确消费 classic/community/experimental 兼容组。SQL 模型改走 ChatOpenAI，模型生成的 SQL 使用只读 SQLite 连接，并有拒绝 DELETE 的负例。

启动示例（本轮未做 UI 浏览器验收）：

```bash
"$S01_AGENT_VENV/bin/python" -m lib_graph.langgraph_hello
MCP_PORT=8001 "$S01_AGENT_VENV/bin/python" -m mcp_server_math.main
MCP_PORT=8000 "$S01_AGENT_VENV/bin/python" -m mcp_weather.main
"$S01_SERVER_VENV/bin/uvicorn" app.server:app --app-dir server --port 8080
```

## 5. 验证命令

```bash
"$S01_AGENT_VENV/bin/python" -m pytest tests/s01/test_native_features.py tests/s01/test_mcp.py tests/s01/test_existing_workflows.py agent_muti_discussion/src/tests/test_discussion.py -q
"$S01_SERVER_VENV/bin/python" -m pytest tests/s01/test_langserve.py -q
"$S01_UI_VENV/bin/python" -m pytest tests/s01/test_ui_rag.py -q
```

以上为确定性回归，模型/Embedding 使用 fake 或 HTTP MockTransport，MCP 使用真实本地协议。另行执行下列脚本会使用本地凭据访问真实 provider，并覆盖对应冒烟回执：

```bash
"$S01_AGENT_VENV/bin/python" tests/s01/live_smoke.py
"$S01_AGENT_VENV/bin/python" tests/s01/live_mcp_smoke.py
```

前者覆盖文本、流式、结构化结果，后者覆盖真实模型到本地 HTTP MCP 计算工具的完整往返。结果范围及未验证项见 [复盘](run-01/03-review.md)，恢复方法见 [回滚说明](rollback.md)。
