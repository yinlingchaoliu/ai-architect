# 07 · 当前项目接入与渐进迁移

日期：2026-11-12。状态：**reviewed / self_review，实施计划未执行**。本章仅规划 LLM v2 内部切片，不重排 S02–S11，也不修改其方案。将来若需调整其他 task，先提出具体差异并由用户确认。

## 1. 迁移原则与最小切片

先交付可独立调用的模型层，再让原生 LangChain Agent/Graph 消费，最后逐入口替换 SDK。每个消费者一次只选择一个调用后端，避免“新 LLM 已接入但真实请求仍走旧 client”。真实切换后的 token/attempt/request_id 回执才证明接入。

默认保留当前 `deepseek-flash` 非思考行为；思考回放是独立能力门槛，不为了迁移切片引入新模式。先用确定性 adapter 和本地 HTTP 验证机制，再在获准范围内调用 provider；本轮没有实施这些阶段。

## 2. 可运行阶段及重要文档

| 阶段 | 实际实现写集（未来授权后） | 可运行切片 | 必须生成的重要文档与验收 |
|---|---|---|---|
| L0 固定合同 | LLM v2 DTO/Protocol、配置 schema、provider descriptor；测试夹具 | 无模型也能校验合法/非法配置、类型和 revision | `run-02/contract-baseline.md`；输入/字段/错误/能力与批准写集固定 |
| L1 最小 runtime | facade/kernel、现有 OpenAI-compatible adapter、TransportPool、本地准入、外层 BudgetPort 测试实现 | 单次 achat + stream + complete/close；模拟 timeout/retry/unknown usage | `run-02/runtime-verification.md`；连接复用、泄漏、取消、准入上限与 reserve/settle 负例 |
| L2 原生 LangChain | ManagedChatModel、bind_tools、structured、sync bridge | LCEL、create_agent+工具、StateGraph、同步旧入口共用内核 | `run-02/langchain-contract-report.md`；工具绑定后无旁路；结构化/流/回调不重复计账 |
| L3 首批业务接入 | lib_graph demo、agentmcp、Manus 兼容门面；随后会议/旅行/讨论入口 | 原行为保持，真实请求通过统一 kernel，工具执行仍在上层 | `run-02/consumer-migration-report.md`；逐入口映射和新旧差异、有限真实模型验证 |
| L4 服务与多副本 | LangServe/WebUI/CSV 注入、shared QuotaBackend、部署生命周期与观测 | 多 worker 共用一个 account 配额，长流与慢客户端隔离 | `run-02/concurrency-and-capacity-report.md`；负载条件、原始值、失败/未知及配额故障演练 |
| L5 Provider 扩展 | 专用 DeepSeek LangChain adapter、replay codec；其他 provider 工厂 | thinking + tool 多轮仅在验证 profile 中启用；第二 provider 不改 kernel | `run-02/provider-compatibility-report.md`；消息/参数/replay/usage 对照和受控真实调用 |

`run-02` 是**建议的后续实施记录位置**，本轮不创建空执行结果。每阶段内部都记录思考、行动、复盘和反思；失败未解除不能将依赖它的能力标为完成。L5 不阻塞默认非思考路线，但它未通过时不能启用 thinking+tools。

## 3. 按当前调用方迁移

| 当前调用方 | 最小接入方式 | 同时移除/保留 | 必需反馈 |
|---|---|---|---|
| lib_graph `build_agent` | model 注入 `llm.chat_model(profile)`；保持其签名可接原生模型 | 保留 ModelCallLimitMiddleware/Graph；删除 demo 重复 ChatOpenAI 构造 | 工具多轮、context、call/attempt ids |
| agentmcp | 继续 MCPAdapter context；model 改 ManagedChatModel | MCP 发现/调用不搬到 LLM；model 参数依赖注入继续可测试 | 真实本地协议 + 模型治理都生效，错误清理不吞 |
| Manus LLMManager | 先写 compatibility facade，将旧 messages/tools 映射到统一 generate | 原业务 plan/execute 图保留；退出本地 SDK/重复 retry 和可变总账 | 返回 content/tool_calls/usage 合同；unknown 不改成零 |
| 会议 graph | 先通过 sync bridge 维持同步图，再单独 async 化需要的节点 | 保留业务提示词/角色；停止返回“思考中…”伪成功 | SDK 失败会让正确节点失败；原消息解析保持 |
| agent_muti | 构造时注入 LLMClient/profile，`_call_llm` 只调用一次统一模型层 | 删除每 Agent 的 AsyncOpenAI 和本地请求重试 | deadline 真正覆盖请求；逻辑迭代仍由原协调器拥有 |
| agent_muti_discussion | 将模型调用注入；消息历史由原 session/agent owner 显式传入 | 不把会话搬进 LLM；异常不变普通错误字符串 | 不同 session 不共享可变消息；同步/异步路径分别测试 |
| MCP manager/router | 模型决策调用统一 LLM；工具 schema 输入/结果输出保持 | 不将 MCP 工具执行合并进 provider adapter | 错误分类、tenant/run 关联与工具 loop 各自清楚 |
| LangServe | lifespan 注入 model，route chain 消费 ManagedChatModel | 保留既有 API，仍独立运行其依赖环境 | Schema/invoke/stream、disconnect、服务退出 |
| WebUI/PDF/CSV | 构建链时注入 model；旧 chain 类型暂留兼容组 | SQL 只读边界保留，Embedding 不被替换成 chat 模型 | 检索来源、SQL 结果、UI 错误与模型错误分开 |
| lib_request 旧客户端 | 视调用方需求选择兼容 facade，明确弃用周期 | 不让新接口和旧 requests 同时发一次业务请求 | 选定后端与实际请求计数一致 |

Manus 旧 cost/usage 字段若不能表示 null，需要同时调整其直接消费者或显式新增 unknown 状态；不能为了兼容旧数值类型伪造零费用。这是本阶段需评审的具体合同差异，不靠适配器静默掩盖。

## 4. 三种接入示例

以下均为拟建 API，用来约束实现，不是已可执行片段。

```python
# 普通业务：不创建 Agent。
message = await llm.achat("整理这份需求", profile="default", context=ctx)

# 旧 Agent：构造一次模型视图，调用时作用域传入，不存 tenant 到 model 上。
class RequirementAgent:
    def __init__(self, llm):
        self.llm = llm
        self.model = llm.chat_model("default")

    async def analyze(self, messages, ctx):
        async with self.llm.scope(ctx):
            return await self.model.ainvoke(messages)

# 原生链：prompt 和输出 parser 仍由调用方拥有。
chain = prompt | llm.chat_model("default") | StrOutputParser()
async with llm.scope(ctx):
    text = await chain.ainvoke({"question": question})
```

StateGraph 节点接收依赖注入 model，同样调用 ainvoke 并返回原生消息；不把 Graph state 交给 LLMRuntime 储存。Graph 的 interrupt 发生在工具/流程边界，kernel 不捕获为模型失败重试。

## 5. 通用模型层的扩展范围

本版完整定义 **chat/text generation、工具调用、流式和结构化输出**，通过 content blocks 和 capability 留出多模态入口。不将 text、Embedding、图像生成和语音统一伪装成一个 chat 返回值。

未来 EmbeddingPort 复用 catalog/secret/transport/admission/usage 生命周期，但使用 LangChain Embeddings、embedding task_kind、向量维度、批量上限和独立结果合同；其 profile 不能传给 chat_model。音频/图像生成同样新增专属 operation invoker，复用治理而不返回假 AIMessage。是否实施由实际 RAG/多模态需求决定，本轮不为它们创建空运行模块。

## 6. 发布、切流与回滚

实施时按单入口/少量租户 profile 指定新 backend 或旧 backend，一次业务调用只走一个；生产影子双发会增加费用和数据外发，不作为默认验证。先比较确定性 fixture 和协议快照，再按已授权真实范围验证。

回滚是新调用回到已保留的入口绑定/旧 provider profile；在途流继续原快照或有界取消，不在中间接一段旧回答。保留 call/attempt 和 unknown usage 事实。不同 codec/provider 的历史 replay 未确认兼容时不恢复到另一 provider。

代码与配置回滚分开：源码恢复只涉及批准的消费者写集；catalog 发布新 revision 指回旧绑定；连接按 drain 生命周期释放。依赖候选按实施时根 requirements 和实际安装证据固定；保留可复现旧候选，不能把历史 [S01 概览](../../01-langchain-upgrade.md)的多组 requirements 当当前仍存在的路径。不得批量恢复其他 task 的用户改动。

每阶段完成条件：入口真实消费统一 LLM、成功/失败/取消均可解释、观察和计账无旁路、重要文档与回执齐全、回滚范围明确。目录和类存在不作为完成依据。
