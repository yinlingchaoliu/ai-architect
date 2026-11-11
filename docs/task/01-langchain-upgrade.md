# S01 · LangChain 升级方案与验证记录

状态：planned（方案已写，未安装或升级依赖）。前置：无。**这是第一项实施工作**；环境盘点和旧行为基线属于本步骤内部，S02 平台开发必须在本步通过后开始。

## 1. 目的与版本决定

将仓库中仍被使用的 LangChain 消费模块升级到当前稳定 **1.x** API 体系，配套采用 LangGraph 1.x 和经过解析、回归的集成包。主流在本计划中指官方当前稳定 API 路线，不代表已测得社区使用占比。核验日期为 2026-11-12；PyPI 当前 LangChain 稳定发布为 **1.5.0**，作为首选验证候选，而不是未经测试的生产锁定结果。该版本要求 Python `>=3.11,<4`；项目选择 Python **3.12** 系列，具体 patch 在执行时固定。[版本与 Python 要求](https://pypi.org/project/langchain/1.5.0/)

不能从 `langchain 1.5.0` 推导所有包都应使用 `1.5.0`。需要对完整依赖集合求解和锁定。本次只阅读官方文档和 PyPI 元数据，**尚未执行依赖求解、pip check 或应用兼容测试**。

## 2. 当前依赖与代码问题

| 实际来源 | 静态观察 | 升级动作 |
|---|---|---|
| [根 requirements](../../requirements.txt) | 多数 LangChain/MCP/模型包无版本；混合 UI、RAG、服务与工具；含标准库 `asyncio` | 拆分消费组与约束，清除不应安装的标准库项，明确每组入口和锁 |
| [graph_discussion requirements](../../graph_discussion/requirements.txt) | `langgraph==0.0.52`、`langchain-core==0.1.42`、`langchain-openai==0.0.8` 等旧约束 | 先保存旧基线，再迁移图、消息、工具接口；检查 NumPy/FAISS 等在 Python 3.12 的实际 wheel/依赖 |
| [server pyproject](../../server/pyproject.toml) / [锁文件](../../server/poetry.lock) | Python 精确 3.12.6；锁中 core/openai 为 1.0.1、LangServe 0.3.3、Pydantic 2.12.3 | 不能称全仓都在旧版；更新到通过联合验证的约束并重生成锁 |
| [web_search.py](../../webui-chatbot/src/pages/web_search.py) | 仍使用 `langchain.schema`、`langchain.text_splitter`、`langchain.globals` | 迁移到 core、text-splitters 或必要的 classic 兼容路径，检查 Streamlit 行为 |
| [agentmcp.py](../../agentmcp/agentmcp.py) | 已用 classic 的 AgentExecutor/create_tool_calling_agent | 比较 v1 `create_agent`；迁移输入、输出与消息历史，保留工具调用行为 |
| [pdf_search.py](../../webui-chatbot/src/pages/pdf_search.py) / [CSV 查询](../../csv-search/llm.py) | 旧检索链使用 classic；SQL 示例使用 experimental | 允许有期限的兼容 Adapter，分别锁定依赖并验证；不能只删除导入来让检查通过 |
| [图 Agent](../../graph_discussion/agents/base_agent.py)、[Manus](../../manus/src/llm/manager.py)、讨论系统、公共库 | 有框架消息，也有原生 OpenAI 调用 | 区分框架和 SDK 类型；验证字符串/内容块、同步/异步、流式和错误映射 |
| [MCP 客户端](../../mcp_client_manager/src/core/mcp_client.py)、天气/数学服务 | FastMCP Client 与 MCP SDK FastMCP 并存，当前服务用 SSE | SDK 版本、import、transport 和资源释放联合验证，不盲升大版本 |

声明、锁文件和实际安装版本是三个事实，S01-A 必须分别采集。当前解释器是否与声明一致需在执行时检查，不根据某个终端的 `python3` 推断所有子项目运行环境。

## 3. 首选候选版本矩阵

以下来自核验当日的 PyPI 版本与 `Requires-Dist`；**是候选集合，不是已验证兼容锁**。执行时只选择未撤回的稳定版本，核对新公告；最终改动必须写精确锁和 hash。

| 包/环境 | 首选候选或约束 | 选择依据与处理 |
|---|---|---|
| Python | 3.12.x，patch 待固定 | 对齐当前服务/工具环境；满足新版 core 要求 |
| `langchain` | [1.5.0](https://pypi.org/project/langchain/1.5.0/) | 要求 core `>=1.8,<2`、LangGraph `>=1.2.12,<1.3` |
| `langchain-core` | [1.8.0](https://pypi.org/project/langchain-core/1.8.0/) | 配套候选；Python 最低 3.11 |
| `langgraph` | [1.2.20](https://pypi.org/project/langgraph/1.2.20/) | 位于 LangChain 1.5 的要求区间 |
| `langchain-openai` | [1.7.4](https://pypi.org/project/langchain-openai/1.7.4/) | 要求 OpenAI SDK `>=2.45.0`；同时检查原生 SDK 消费模块 |
| `openai` | 优先解析 `>=2.45,<3` 中可用稳定版本 | 减少额外 SDK 大版本迁移；最新 3.x 不自动加入，本步验证后锁定补丁 |
| `pydantic` | [2.14.3](https://pypi.org/project/pydantic/2.14.3/) | 保持 2.x，配合 core、MCP 和 FastAPI 联合验证 |
| `langchain-community` | [0.4.2](https://pypi.org/project/langchain-community/0.4.2/) | 仅在 FAISS/SQL 等实际使用处引入，不并入最小内核 |
| `langchain-classic` | [1.0.8](https://pypi.org/project/langchain-classic/1.0.8/) | 遗留链过渡；不成为新平台业务编排方式 |
| `langchain-text-splitters` | [1.1.3](https://pypi.org/project/langchain-text-splitters/1.1.3/) | 替换旧 text_splitter 导入 |
| `langserve` | [0.3.3](https://pypi.org/project/langserve/0.3.3/) | 元数据允许 core `<2`，仍需实际路由/Schema/SSE 回归 |
| `langchain-mcp-adapters` | [0.3.2](https://pypi.org/project/langchain-mcp-adapters/0.3.2/) | 元数据要求 `mcp>=1.24,<2` |
| MCP SDK / FastMCP 兼容组 | [mcp 1.30.0](https://pypi.org/project/mcp/1.30.0/) + [fastmcp 2.14.7](https://pypi.org/project/fastmcp/2.14.7/) | 与上述 `<2` 约束有交集，需验证现有 SSE/Client 接口；不是要求独立服务永远停在旧系列 |
| `langchain-experimental` | [0.4.2](https://pypi.org/project/langchain-experimental/0.4.2/) | 只给 CSV/SQL 遗留示例，限制 SQL 权限并测试结果 |
| PostgreSQL checkpointer | [3.2.0](https://pypi.org/project/langgraph-checkpoint-postgres/3.2.0/) | S01 只记录候选；S04 才接入并固定与 checkpoint 的组合 |

已发现的明确约束冲突：当前 MCP SDK 最新稳定版为 [2.3.0](https://pypi.org/project/mcp/2.3.0/)，不能与要求 `<2` 的 adapters 0.3.2 直接放进同一环境。独立 MCP 服务以后可用不同 SDK 经协议互通，但必须分别锁定并测协议；本步默认先采用有交集的 1.x 兼容组。[adapters 元数据](https://pypi.org/pypi/langchain-mcp-adapters/0.3.2/json)、[FastMCP 元数据](https://pypi.org/pypi/fastmcp/2.14.7/json)

## 4. 任务顺序与写集

| ID | 任务 | 预期写集/产物（实施时创建） | 完成证据 |
|---|---|---|---|
| S01-A | 记录各入口解释器、声明、锁和已安装包；采集旧行为 | 本文的基线记录、脱敏输入/输出、缺陷清单 | 已观察/未观察、既有缺陷与升级回归分开 |
| S01-B | 建立隔离 Python 3.12 环境和候选约束 | `requirements/constraints-langchain.txt`、MCP 兼容组、各消费项目锁 | 依赖求解、可复现安装、`pip check`；server 同步更新 Poetry 锁 |
| S01-C | 优先升级 core / provider / LangGraph 消费代码 | `graph_discussion`、`lib_graph`、`server`、相关消息处理 | 导入、图终止、序列化、路由和模型响应合同 |
| S01-D | 迁移工具 Agent 与遗留链 | `agentmcp`、WebUI 检索/搜索、CSV/SQL 和对应依赖声明 | 工具循环、检索结果、SSE、会话行为不丢失 |
| S01-E | 验证原生 SDK 消费者及 MCP | 讨论系统、Manus、`agent_muti`、MCP 客户端/服务和相关库 | 本地协议闭环、同步异步接口、错误与释放资源 |
| S01-F | 固定最终版本并完成升级文档 | 精确锁、版本矩阵、兼容例外和本文实际结果 | 所有必需入口通过，明确的可选隔离项不冒充已升级 |

约束统一不等于所有子项目同一个虚拟环境：根消费清单说明各入口应使用哪组环境，原 server 暂保留 Poetry；S02 新平台使用独立 `uv.lock` 并继承本步验证过的公共依赖合同。LlamaIndex/本地大模型的独立依赖不在本步强制升级，但跨边界的输出合同必须保持。

## 5. API 与行为迁移决定

官方 v1 收敛了包命名空间，遗留 chains 等移到 classic，推荐新 Agent 使用 `langchain.agents.create_agent`。现有自定义 `StateGraph` 保持图式建模，不为升级强行全部重写。内容块、工具循环、输入输出键和流事件都需按当前业务合同转换。[LangChain 迁移指南](https://docs.langchain.com/oss/python/migrate/langchain-v1)、[LangGraph 迁移指南](https://docs.langchain.com/oss/python/migrate/langgraph-v1)

| 场景 | 迁移方式 | 防回归要求 |
|---|---|---|
| 旧消息/切块导入 | core messages / 独立 text-splitters；其余使用明确兼容层 | 真正执行调用，不能只用 import 成功判断 |
| AgentExecutor 工具循环 | v1 create_agent 与 messages 输入；在边界适配最终消息/工件 | ToolMessage、tool_call_id、多次工具调用、失败和最大步数 |
| LangGraph 状态与消息 | 明确 TypedDict、reducer、thread/checkpoint 作用域 | 同轮追加不丢失、不重复，终止和异常不吞没 |
| `.content` 使用 | 区分纯文本、列表/内容块和原生 SDK 对象 | 不把结构化结果 `str()` 后冒充合法业务 JSON |
| LangServe 与 Pydantic | 验证 invoke/stream、Schema、现有 API 合同 | LangServe 可用不代表平台任务 API 已完成 |
| 旧检索链和 SQL 链 | 遗留 Adapter 中保留必要 classic/experimental，登记后续迁移负责人和 S10 去向 | FAISS 构建/查询、SQL 只读约束、来源和错误保持 |

community 可能传递依赖 classic；退出条件限制的是平台业务直接使用旧编排 API，不以“依赖树中完全没有 classic”为不切实际的目标。

## 6. 验收和回滚

- 必需：干净环境可从精确锁安装，依赖检查无冲突，根/子项目入口使用的依赖合同一致且可追溯。
- 会议图与 Manus：固定 fake 模型/工具验证成功、失败、最大轮次、消息和结构化输出；既有“失败仍完成”等问题记录为基线缺陷，本步仅在兼容确需时修复，业务修正留 S03/S04。
- 服务/UI：路由、Schema、invoke/stream、会话与检索通过；不能以 mock 模型结果声称外部模型兼容已通过。
- MCP：独立本地进程发现工具、调用、关闭，检查实际 SSE/选定 transport；天气提供者可 stub，不能据此证明真实天气 API 正常。
- 真实模型：在获准可用的 provider 上做限额内冒烟，核对文本、工具、流和 usage。未运行则该项 not_run，候选只能标为“本地兼容通过”，不能标完整升级验收。

任一必需入口不通过，不进入 S02 的正常迁移。允许继续调查或提出明确的隔离方案，但不能悄悄退到旧 core 仍报告全仓升级完成。候选失效时更新本文说明选择与取舍，不使用运行时 `latest`。

回滚：停止升级候选入口 → 保留失败输入/日志 → 恢复对应源码、解释器和原锁 → 在隔离环境重建 → 重跑旧基线。不得把旧包覆盖安装进已混用的新环境；本步不引入业务数据库迁移。

## 7. 本步重要文档的实施补记

执行时在本文追加：实际版本矩阵和 hash、候选与最终差异、修改文件、各入口回归结果、真实外部冒烟结果、兼容保留项与 S10 退出计划、回滚演练和结论。当前均为 **not_run**。文档要求见[总计划 §5](README.md#5-步骤与文档完成标准)。
