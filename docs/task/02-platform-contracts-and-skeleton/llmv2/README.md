# LLM v2：基于 LangChain 的通用模型层

日期：2026-11-12（Asia/Shanghai）。文档状态：**reviewed / self_review，待用户评审**；实现状态：**planned**。本轮只设计，未改造运行代码、依赖或其他 task。输入为当前项目源码、相邻 `deepseek-harness` 的 LLM 源码与本轮官方资料；**没有读取或沿用 `02-platform-contracts-and-skeleton/llm` 方案**。

## 1. 建议采用的架构

采用一个可嵌入 Python 应用的 LLM 库，内部按职责分层：**易用 API / LangChain Bridge → 调用内核 → Provider Adapter → LangChain 集成与 HTTP 连接池**。模型、连接和策略配置通过独立控制面注册、发布和固定 revision。Agent Harness 与 Graph 位于通用模型层之外。

- **Harness** 管 Run/Task、授权、总预算、上下文、工具执行及恢复。
- **Graph / create_agent** 管节点、分支、状态、工具循环和 checkpoint。
- **LLM** 管一次逻辑模型调用：选择已授权模型、固定配置、容量准入、物理请求尝试、流和 usage、错误、取消及连接释放。
- **LangChain/provider SDK** 提供原生消息、工具 schema、模型接口和线上协议。优先复用，项目仅补治理与 provider 兼容边界。

这使简单调用和复杂图共用一条模型调用治理链，避免引入另一套 Agent 运行循环。逻辑分层首先落在一个库内；没有容量证据前不增加独立模型网关网络跳转。

[拟建 LLM 逻辑层次图源](diagrams/layers.mmd)

图源见 [分层图](diagrams/layers.mmd)，文档内可读 Mermaid 见 [架构设计](02-layered-architecture.md)。图均为拟建方案，不是当前已实现架构。

## 2. 接入体验

下列 `agent_platform.llm` 为**拟建接口**，当前不能直接 import。完整签名、请求上下文、生命周期与失败行为见 [API 合同](03-contracts-and-api.md)。

```python
# 应用启动时创建一次 llm，应用关闭时 aclose；每次请求不重建客户端。
message = await llm.achat("请总结这份需求", profile="default", context=ctx)
print(message.text)

# 保持 LangChain 原生模型体验；模型视图按已发布配置 revision 复用。
model = llm.chat_model("default")
agent = create_agent(model=model, tools=tools)
async with llm.scope(ctx):
    result = await agent.ainvoke({"messages": messages})
```

`ManagedChatModel` 保持 `BaseChatModel`，`bind_tools`、LCEL、`ainvoke`、`astream` 与 `create_agent` 都进入同一内核。身份和总 deadline 由服务/Harness 注入，模型不能从 prompt 声明自己所属租户。配置热更新对新绑定生效，长寿命已编译图的配置切换必须由 Graph 所有者明确重建/切换，不能在多步推理中偷偷漂移。

## 3. 文档导航

| 文档 | 评审问题 |
|---|---|
| [01 源码依据与借鉴](01-source-reference.md) | deepseek-harness 具体借鉴什么；当前项目哪里需要统一 |
| [02 分层与模块架构](02-layered-architecture.md) | 职责、依赖方向、代码目录、部署和扩展边界 |
| [03 公共合同与易用 API](03-contracts-and-api.md) | 消费接口、消息、流、错误、usage、调用身份 |
| [04 LangChain 与 Provider 封装](04-langchain-and-provider.md) | 原生 Graph/Agent 如何接入；DeepSeek 思考回放如何保证 |
| [05 高并发与可靠性](05-concurrency-and-reliability.md) | 连接复用、限流、背压、重试、取消和横向扩展 |
| [06 配置发布与生命周期](06-config-and-lifecycle.md) | 动态注册、不可变快照、密钥轮转、在途请求与回滚 |
| [07 当前项目接入与迁移](07-integration-and-migration.md) | 每个入口如何渐进切换；可运行切片、重要文档与回滚 |
| [08 验收、容量验证和决定](08-validation-and-decisions.md) | 需求覆盖、测试矩阵、性能实验、取舍及未知项 |
| [示例合同](examples/contracts.py)、[配置示例](examples/profiles.yaml) | 实施合同示意；不是已实现模块或生产默认配置 |
| [本轮思考/行动/复盘/反思](run-01/README.md) | 本轮实际读取、检查和未执行事项 |

## 4. 本轮结论和范围

关键源码发现：当前通用 `ChatOpenAI` 消息序列化不会回传示例中的 `reasoning_content`，本轮零网络 payload probe 已证实。因此默认 `deepseek-flash` 路线延续显式非思考模式；思考 + 工具必须通过专用 LangChain provider adapter 的请求回放测试后启用，不能只改一个 thinking 开关。

当前没有生产 QPS、模型配额、TTFT、平均输出长度或并发负载样本。本文给出容量模型、候选参数和验收方法，**不承诺未经测量的高并发数值**。高性能来自异步 I/O、连接复用、有界准入和减少重复工作；实际吞吐受 provider 配额与生成速度约束。

本轮未开始 LLM 实施；未调用真实收费模型或执行压力测试；原有其他文档和用户未提交改动保留。完整事实、审阅和候选指纹见 [本轮复盘](run-01/03-review.md)。
