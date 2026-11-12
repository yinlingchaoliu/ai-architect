# 04 · LangChain Bridge 与 Provider 封装

日期：2026-11-12。状态：**reviewed / self_review，拟建**。框架依据为本轮读取的 core 1.8.0 `BaseChatModel`、LangChain 1.5.0 create_agent factory 及候选 provider 源码；准确版本/指纹见 [源码依据](01-source-reference.md)。

## 1. 保留 LangChain 原生能力

原生标准类型直接作为本模块模型边界：BaseChatModel、BaseMessage、AIMessage、AIMessageChunk、ChatResult/ChatGenerationChunk、RunnableConfig、BaseTool schema。它们解决消息/工具/内容块、链组合和模型运行协议；平台只补注册、配置、容量和调用生命周期。

`ManagedChatModel(BaseChatModel)` 是轻量桥接器，内部持有 `ModelBinding` 和 runtime handle（不可序列化 PrivateAttr），不是新的 AgentExecutor。它的下游是私有 underlying model，后者由 provider 工厂构建并复用。

| LangChain 面 | 拟建处理 | 必需验证 |
|---|---|---|
| `_agenerate` | 交给 kernel.complete，转为 ChatResult；不吞错误 | ainvoke、usage、provider id/metadata 保真 |
| `_astream` | kernel.open_stream → ChatGenerationChunk；finally 关闭 | astream、工具参数、reasoning、尾部 usage、提前关闭 |
| `_generate/_stream` | 显式同步兼容桥到同一 async kernel | 旧 invoke/stream；禁止在 owner event loop 内阻塞 |
| `bind_tools` | 校验/冻结 schema，返回保持 ManagedChatModel 的新绑定视图 | create_agent 再次绑定时不退回 raw model；嵌套 schema 保留 |
| `bind` / `with_config` | 维持 Runnable 组合；受控 kwargs 在 kernel 校验 | 调用者不能用 extra_body 覆盖 endpoint、timeout 或 retry |
| `with_structured_output` | 支持的 method 显式选择，所有模型调用继续经过 Managed 视图 | include_raw、校验失败、工具/原生 schema 差异 |
| `profile` / model_name | 暴露固定 revision 的能力和真实身份 | create_agent 的 capability 判断和实际 provider 一致 |
| `batch/abatch` | 有界并发和输入上限，每项独立准入 | 不绕过 quota，不创建无界 task |

BaseChatModel 的内部扩展方法是项目需要维护的框架接口，不声称未来所有版本零成本兼容。当前 core 的 model.profile 仍带 beta 标记，因此默认采用显式 ToolStrategy，并将该能力字段列入版本回归。桥接集中在单模块、固定版本并做合同行为回归；不全局 monkey-patch 框架。

## 2. 一个请求只能有一个治理所有者

调用链固定为 ManagedChatModel → kernel → AdapterHandle → 原生 provider model → SDK/HTTP。原生 provider 设置 `max_retries=0`，不再装 provider rate_limiter 或 `.with_retry()`；排队、限流、deadline 和物理 retry 统一由 kernel 负责。

Managed 与 underlying 模型的 LangChain `cache=False`，防止全局模型缓存绕过准入、身份和预算。默认只缓存连接、模型构造和能力 metadata，不缓存用户回答。未来响应缓存必须位于 kernel 授权之后，并明确 tenant、model revision、工具/schema、provider replay、usage 和未发网状态。

LangChain 的 native callbacks 仍服务 trace；wrapper 和 provider 可能有父子模型 span。UsageSink 只按 physical attempt_id 记一次事实，不能用两层 on_llm_end 各记一次账。使用框架 run_manager 传递 child callback，token 回调只选择一个公开边界；不向用户同时转发两条重复流。

模型 binding 中不存 request identity、messages 或 mutable headers；工具绑定是不可变视图。SDK/HTTP 客户端的关闭权限只属于 TransportPool；不能由一次 Runnable 的退出关闭共享 AsyncClient。

原生 callback 与外部遥测不是同一边界：Graph 内部需要的原生模型事件可以保留完整对象，外部 exporter 必须经过内容投影与脱敏。composition root 检查 LangChain/LangSmith 的自动 tracing 配置，默认关闭未经批准的正文上报；显式传入的 exporter 也需审核，不能只修改 metadata 就声称 prompt/reasoning 已隐藏。LLM 无法替一个已经在外层完整导出 Graph state 的应用做全局隐私保证。安全错误的公共异常链不携带原始鉴权请求/headers，受限诊断通过关联 id 保留必要事实。

## 3. 原生 create_agent / Graph 接入

```python
# 拟建 API。应用启动后复用 model/agent；不是每次请求重新 compile。
model = llm.chat_model("default")
agent = create_agent(
    model=model,
    tools=tools,
    middleware=[ModelCallLimitMiddleware(run_limit=8)],
    response_format=ToolStrategy(Answer),
)

async with llm.scope(ctx):
    result = await agent.ainvoke({"messages": messages})
```

ModelCallLimitMiddleware 管 Agent 逻辑模型步数；LLM kernel 管该步内的物理尝试及配额。外层预算必须同时约束逻辑步和物理尝试消费。ToolStrategy 可能发起结构化修正，它是新的模型调用，继续经过同一 kernel 并消费剩余预算；不是被归为 transport retry。

`scope` 使用 ContextVar 传播关联，进入 executor 的同步桥显式复制上下文。Graph 内新 task/跨进程任务不依靠“应该继承”推断身份；由 Harness 显式绑定。没有可信调用上下文的生产 native 调用在发网前拒绝。

长期图绑定固定模型能力/config revision，避免 `model.profile` 编译时支持原生 schema、运行时 alias 却换成不支持的 provider。profile 发布后：普通 direct 调用的新 binding 读取新 revision；Graph 所有者预编译/验证新 binding 对应图并切换新 Run 的图引用。LLM 发变更通知但不替 Graph 编译或修改在途 Run。明确切模型需记录新绑定及 replay 兼容决定。

## 4. DeepSeek 路线与能力门槛

### 4.1 第一条可实施路线

默认 `deepseek-flash` + Chat Completions + **显式 thinking disabled**，复用现有 ChatOpenAI 集成，HTTP 与 SSE 仍由 LangChain/SDK 处理。S01 已有有限真实验证可作为回归输入，但本设计并未重新执行这些历史测试。

这是一个注册的 provider profile，不根据 `model.startswith("deepseek-")` 在各个 Agent 类散落分支。思考开关和模型参数由 provider adapter 统一映射，实际请求参数写入脱敏 effective-config 信息。

### 4.2 专用 LangChain DeepSeek adapter

候选采用 `DeepSeekChatModel(ChatDeepSeek)` 的窄兼容扩展，基于本轮源码检查的 `langchain-deepseek 1.1.1`。基础能力由官方集成提供；项目只补以下经测试确认的缺口，不重新实现完整 SDK、SSE 或重试：

1. 请求携带 tools 时，按当前 DeepSeek 协议保留所需历史 assistant 的 reasoning_content，不只看这一条 assistant 是否带 tool_calls。
2. 从完整 AIMessage 和 chunk 保存原始 provider replay 字段；不能从 `.text` 或 UI 安全投影重新构建下一轮历史。
3. 保留工具 id、名称、raw arguments 和工具结果角色，确认空 assistant content 的 wire 规则；不擅自用占位内容改变语义。
4. thinking mode=on 时校验 effort 和无效采样参数；未知配置拒绝，不声称 low/high 在所有 provider 等价。
5. `strict=True` 不允许集成库静默转 beta endpoint。只有配置明确允许 beta 并固定该 endpoint/protocol revision 时才启用；否则发网前拒绝。
6. 流式 usage、cache 和 finish 的实际映射独立测试。

当前 generic ChatOpenAI payload probe 已证明 reasoning 字段不会透传；候选 ChatDeepSeek wheel 可见 reasoning 提取，但不能据此证明请求回放齐备。必要时在专用子类的 `_get_request_payload` 窄钩子补齐，并将这个版本相关钩子列为升级回归点。未通过 mock wire replay + 真实受控多轮工具验证前，capability `thinking_tool_replay` 不得标 supported，默认 profile 不能启用该组合。

DeepSeek 官方当前要求与集成页的旧型号说明存在时效差异；能力必须取 provider 线协议、所用集成版本、已验证模式三者交集。模型支持图片不等于某条 adapter 输入路径支持图片。

## 5. Provider 统一而不压平差异

| 变化点 | 公共层 | adapter 层 |
|---|---|---|
| 文字/工具/结构化 | 原生消息和 schema；请求能力声明 | 实际 wire/集成方法与组合限制 |
| thinking | mode + adapter 声明的 effort | extra_body 或原生 reasoning 参数、历史 replay |
| 多模态 | content blocks / 引用；限制 request bytes | provider 与 adapter 双重支持判断；不支持时显式拒绝 |
| finish | stop/tool_calls/length/filter/unknown + 原始值 | 具体 provider finish 证据，不把 EOF 当 stop |
| usage | 总输入/输出和明细子集、nullable | cache/reasoning 定义及 cumulative/delta 规范化 |
| 错误 | 统一 code、阶段和 request_effect | SDK exception / HTTP status / Retry-After 映射 |
| 模型发现 | advisory catalog + allowlist | list_models 或静态 metadata；不允许在请求热路径自动探测网络 |

能力状态是 supported / unsupported / unknown，并携带声明来源和验证 revision。协议兼容的 endpoint 不是 provider 能力声明，未知能力不能静默降级。

## 6. 结构化输出边界

独立 LLM 调用默认 `method="function_calling"`，一轮模型生成后本地 Pydantic 解析；没有真实工具执行，也不为了易用性创建隐藏 Agent。非法结果报错，默认 repairs=0。需要修正时由上层新调用显式消费预算。

create_agent 的结构化输出继续使用原生 ToolStrategy/ProviderStrategy；LLM 不再重复添加一个结构化工具或第二次校验重试循环。ProviderStrategy 只在 profile 明确支持对应 schema 及与工具共用模式时启用，不能从模型名猜。只要求 JSON 字符串的 json_mode 不等于严格 schema 验证。

## 7. 同步兼容与生命周期

异步服务在自己的 owner event loop 创建并复用 LLMRuntime。同步旧节点在线程中通过桥调用 owner loop 的 async kernel，不能在该 owner loop 里调用 `.result()` 阻塞自身。检测到同步调用位于运行中的同一事件循环时明确报 SYNC_IN_EVENT_LOOP，要求使用 ainvoke。

纯同步 CLI 可在启动时创建一个专用 portal/event-loop 线程，客户端在该线程创建和关闭；不是每次请求 asyncio.run。同步流通过有界跨线程通道转发，consumer close/timeout 会取消生产 task 并 await aclose；终态走独立信号，不因队列满而丢失清理。运行时代码需避免从同步 worker 将同一 AsyncClient 搬到另一 loop。

这条兼容桥是迁移工具；高并发 HTTP/Graph 主路径使用 native async。测试覆盖 ContextVar/调用身份传递、stream 早退、portal 退出和线程数量稳定。同步桥不拥有第二份 provider 全额配额或独立的预算执行权。
