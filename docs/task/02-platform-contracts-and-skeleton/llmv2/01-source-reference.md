# 01 · 源码依据与 deepseek-harness 借鉴

日期：2026-11-12。状态：**reviewed / self_review**，静态源码分析和一项本地机制 probe。候选指纹见 [sources.json](run-01/evidence/sources.json)；目录名或参考测试存在不代表本项目已接入或本轮已运行这些测试。

## 1. 固定输入与阅读边界

当前项目 HEAD：`98425ec910407e447c40d5528e84f445d8c38cc8`，工作区已有用户改动。参考仓库为本地 `../deepseek-harness`，HEAD：`47f943859bef60e4160492346772ded9b24f765a`，本轮读取时无 Git 改动。本地源码优先于二手介绍；没有读取现有 S02 `llm` 方案或其历史设计作为本方案输入。

框架核对使用现有 S01 隔离环境：LangChain 1.5.0、core 1.8.0、LangGraph 1.2.20、langchain-openai 1.7.4、HTTPX 0.28.1。工作区在本轮期间出现并行依赖整理：原 requirements 子目录被删除，根 [requirements.txt](../../../../requirements.txt) 成为精确版本入口，声明 LangServe 不带 server extra，并显式选择 sse-starlette 3.7.0。本文对该变化只核对当前声明，未重复执行统一环境安装/联调；本轮 probe 仍使用原有 S01 独立环境。没有恢复被删除文件或覆盖其他路径。

另读取 PyPI `langchain-deepseek 1.1.1` wheel 中的源文件，核验下载 hash；**仅源码检查，未安装该候选**。其声明 `core>=1.4.7,<2`、`langchain-openai>=1.3.1,<2` 与已装版本有交集；完整新组合求解、安装及 provider 验证仍待实施。

## 2. deepseek-harness LLM 的真实职责

以下链接固定到参考 commit，不依赖 main 分支继续变化。

| 源码位置 | 本轮观察到的行为 | 本项目采用方式 |
|---|---|---|
| [`llm/src/index.ts` LlmRuntime、registerAdapter](https://github.com/deepseek-ai/deepseek-harness/blob/47f943859bef60e4160492346772ded9b24f765a/packages/llm/llm/src/index.ts#L284) | 注册 provider 路由；完整校验后替换；注册有 disposer；模型目录和精确 model 解析分开 | AdapterRegistry + 不可变 catalog revision；目录用于发现，准入另查授权与能力 |
| [PreparedLlmCall / prepareCall](https://github.com/deepseek-ai/deepseek-harness/blob/47f943859bef60e4160492346772ded9b24f765a/packages/llm/llm/src/index.ts#L779) | 固定配置及 adapter registration；配置冻结；stream 一次性消费，检查配置一致性 | 单次 `PreparedCall` 持有 provider 句柄、配置、credential lease 和 lineage；重试不重新漂移选择 |
| [GenerateOptions / StreamChunk](https://github.com/deepseek-ai/deepseek-harness/blob/47f943859bef60e4160492346772ded9b24f765a/packages/llm/llm/src/types.ts#L291) | 请求是一次模型调用；流区分文本、reasoning、工具参数、usage、finish | 复用 LangChain Message/Chunk；外加调用生命周期事件，避免再发明完整消息体系 |
| [BlockAssembler](https://github.com/deepseek-ai/deepseek-harness/blob/47f943859bef60e4160492346772ded9b24f765a/packages/llm/llm/src/assembler.ts#L36) | 按索引组合 delta，处理最终块、usage、finish；工具参数保留原始片段 | 使用 AIMessageChunk 原生组合及 provider 规范化；不在每个 token 上重建整个消息 |
| [DeepSeekAdapter.stream](https://github.com/deepseek-ai/deepseek-harness/blob/47f943859bef60e4160492346772ded9b24f765a/packages/llm/llm-deepseek/src/adapter.ts#L214) | 每次 stream 固定连接与凭据；同一取消信号到 fetch 和读流；finally 关闭迭代器 | 每次调用固定连接快照，应用生命周期复用客户端，取消和提前退出显式释放 |
| [DeepSeek serializeMessages](https://github.com/deepseek-ai/deepseek-harness/blob/47f943859bef60e4160492346772ded9b24f765a/packages/llm/llm-deepseek/src/serialize.ts#L75) | provider 边界负责 assistant/tool 角色、reasoning 和工具参数的 wire 映射 | provider 兼容留在专用 LangChain adapter，不放进 Agent 类 |
| [llm-retry recover](https://github.com/deepseek-ai/deepseek-harness/blob/47f943859bef60e4160492346772ded9b24f765a/packages/llm/llm-retry/src/index.ts#L149) | 重试策略与执行分离；在 agent/request-error 扩展点恢复，带 signal 与退避 | 保留错误分类、策略分离和可取消退避；本项目物理请求重试统一由 LLM kernel 执行，Graph 不叠加同类重试 |
| [agent-loop step](https://github.com/deepseek-ai/deepseek-harness/blob/47f943859bef60e4160492346772ded9b24f765a/packages/core/agent-loop/src/agent.ts#L332) | 上层建立请求、消费 chunk、维护 session 并决定恢复和工具流程 | Harness/Graph 保持控制权；LLM 不成为第二个 session/Agent 控制器 |

参考仓库的 topology、adapter-failure 测试也被定向阅读，用于发现替换和错误边界的测试场景；本轮未运行其 TypeScript 测试。

## 3. 有意识地不照搬的行为

1. **不复制 TypeScript/Cordis 插件框架和原生 fetch/SSE 栈。** Python 使用 LangChain provider 集成及应用装配注册；项目新增内容以治理和小范围兼容为主。
2. **不复制第二套完整消息与 block 协议。** 对外沿用 `BaseMessage / AIMessage / AIMessageChunk / ToolMessage`。只有跨进程/持久化边界使用明确版本的 codec。
3. **不复制 usage 的数值语义。** DSH 的 inputTokens 是不含 cache 的计数；LangChain 的 input_tokens 按总输入理解。本设计的 cache/reasoning 是子集，不能再次相加；映射公式见公共合同。
4. **不把 EOF 自动当 stop。** 参考 BlockAssembler 未收到 finish 时存在 stop 默认值；本项目要求 adapter 提供明确完成证据，缺失时标记 incomplete/protocol_error。
5. **不开放 always 无限重试。** 所有物理尝试受总 deadline、attempt 数和上层预算约束；部分输出之后不自动接另一段生成。
6. **不将 catalog 缺失等同于禁止模型。** DSH 目录是 advisory；本平台另加明确允许范围与能力验证，支持获准的自定义 model id，不靠字符串前缀猜能力。
7. **不逐字复制 reasoning 回传规则。** 参考 serializer 主要在 assistant 带 tool_calls 时附 reasoning；当前 DeepSeek 官方规则要求请求携带 tools 时回传所需历史 assistant reasoning，因此按实际协议和回放测试设计。

## 4. 当前项目接入问题

| 当前源码 | 已确认事实 | 需要补足 |
|---|---|---|
| [lib_graph/runtime.py](../../../../lib_graph/src/lib_graph/runtime.py) `build_agent` | 已基于 create_agent，有模型调用上限；参数接收原生模型 | 保留该入口，将模型构建移交统一 LLM 层，Harness/Graph 不迁入 LLM |
| [langgraph_hello.py](../../../../lib_graph/src/lib_graph/langgraph_hello.py) / [agentmcp.py](../../../../agentmcp/agentmcp.py) | 各自直接构建 ChatOpenAI，显式关闭 DeepSeek thinking | 复用 profile、连接、错误和限额治理，保留原生 create_agent/MCP |
| [Manus LLMManager](../../../../manus/src/llm/manager.py) | 自管 AsyncOpenAI、模型配置和进程内 usage；缺失 usage 置 0；成本字段默认 0 | 用兼容 adapter 接口消费统一调用；unknown 保留 null；总账不依赖可变累计字典 |
| [旅行 BaseAgent](../../../../agent_muti/src/agents/base_agent.py) | 每个实例创建 AsyncOpenAI；自行循环重试；局部 timeout 变量未用于该 create 请求 | 共享 provider 客户端；总 deadline 实际生效；清除多层请求重试 |
| [讨论 BaseAgent](../../../../agent_muti_discussion/src/core/base_agent.py) | 同步 SDK、实例消息历史；部分错误转成普通字符串 | 保留上层会话；LLM 错误保持类型，避免异步路径阻塞 |
| [会议图 BaseAgent](../../../../graph_discussion/agents/base_agent.py) | 同步 invoke；异常返回“思考中…”字符串 | 首期同步兼容桥、后续节点 async 化；异常不伪装内容 |
| [LangServe chain](../../../../server/app/chain/openai_server.py) | 直接暴露 ChatOpenAI Runnable | 注入 ManagedChatModel，保留服务路由和原生 schema |
| [MCP router](../../../../mcp_client_manager/src/core/mcp_router.py) | SDK 决策与工具执行组合在路由器中 | 模型调用统一；工具执行继续留在路由/Graph |

以上是当前静态事实，不据此声称已出现某个并发峰值、内存泄漏或生产事故。

## 5. 本轮本地 probe 和外部资料

用现有 ChatOpenAI、合成 AIMessage reasoning 字段与工具消息构造 request payload，**没有联网、没有真实密钥**。结果保留 tool_calls，却不保留 reasoning_content，见 [probe 回执](run-01/evidence/langchain-payload-probe.json)。它证明当前通用序列化不满足这一回放要求，不是对 DeepSeek provider 的新一轮实测。

读取 `langchain-deepseek 1.1.1` wheel 源码可见其会提取 response/chunk reasoning，但 `_get_request_payload` 未显式补齐该字段的历史回传；结合当前父类行为，不能仅凭包名认定端到端回放成立。该结论仍需实际 adapter 合同测试，不能直接宣布该包所有模式不可用。

官方核对：[LangChain Models](https://docs.langchain.com/oss/python/langchain/models)、[结构化输出](https://docs.langchain.com/oss/python/langchain/structured-output)、[ChatDeepSeek 集成](https://docs.langchain.com/oss/python/integrations/chat/deepseek)、[DeepSeek thinking/tool 历史要求](https://api-docs.deepseek.com/guides/thinking_mode/)、[HTTPX 连接限制](https://www.python-httpx.org/advanced/resource-limits/)、[异步客户端复用/关闭](https://www.python-httpx.org/async/)。集成页仍含旧 model 名和特性表，具体能力以本轮目标模型、实际 adapter 和线协议测试的交集为准。
