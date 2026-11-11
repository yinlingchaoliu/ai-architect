# S03 · 资源与现有 Agent 适配

状态：planned。前置：S02。对应目标：L5。设计依据：[资源与扩展接口](../ai-archtect/01-platform-architecture.md)、[当前调用链](../current-architecture.md)。

## 1. 目标与迁移方式

先把一条现有会议流程接到公共执行合同，再统一模型、MCP、工具、RAG 和沙箱边界。先整图包裹 `graph_discussion`，保留旧结果作为对照；角色拆分与业务策略变化安排在 S06。此阶段本地 Adapter 可以工作，但统一持久调度由 S04 实现。

```text
旧 CLI → 旧会议图                          （保留对照）
平台本地调用 → LangGraphAdapter → 同一会议图 （新增入口，隔离测试数据）
                          → ModelGateway / Tool Adapter
```

## 2. 任务与边界

| ID | 工作 | 主要位置（拟） | 核心要求 |
|---|---|---|---|
| S03-A | 实现 LocalAgentAdapter / LangGraphAdapter | `platform/.../adapters/` | 输入投影、进度、工件、错误、查询/取消能力声明 |
| S03-B | 模型访问收敛 | `resources/models/`；旧 Agent 注入接口 | 模型 profile、secret 引用、超时、stream 和 usage 来源统一 |
| S03-C | 工具与 MCP 绑定 | `resources/tools/`、`resources/mcp/` | list/call/close、Schema、资源释放、权限和 operation_id |
| S03-D | RAG 能力分类 | `resources/retrieval/` | 模拟知识与真实检索使用不同 profile，返回来源和版本 |
| S03-E | 代码/文件执行边界 | `resources/sandbox/` | 独立工作区、资源和出站限制、可观察进程停止 |
| S03-F | 去除全局可变资源耦合 | 受迁移的 Agent/子图 | 新入口按上下文注入；并发任务不共享可变 AgentPool/会话 |

Manus 的失败仍被标 completed、全局 AgentPool，以及图内 LLM 错误被转成普通文字的问题，在 Adapter 边界转为显式失败/未知观察；修正需记录对旧行为的变化。旧模块未迁移部分保持独立，不能因一个 Adapter 成功就宣称全仓已适配。

## 3. 重要决定

Adapter 不另开调度器，不自行重试业务写操作；只提交观察和能力。模型输出经 Schema 校验后才进入公共结果；非字符串 content、工具失败和 usage 不可见均保留类型/unknown。

数学和 Python 工具不把主机进程或 `eval` 当安全沙箱。暂未完成隔离的工具在新平台禁用，保留旧代码为示例，不进入可用能力列表。真实 RAG 的索引/模型不在本步重建，先固定检索 port 和可信来源口径。

## 4. 验收与回滚

固定输入验证会议旧入口与 Adapter 的输出结构、轮次、终止和异常；fake 模型测试只能证明流程合同。MCP 用独立本地进程测试工具发现、嵌套参数、错误和关闭；验证两个并发会话不串数据。对超时工具检查实际进程/回执，不能只观察协程抛异常。

回滚按 Adapter/资源 profile 禁用新入口，回到原独立应用；先排空已发出的工具操作并对账。保留公共 port，不要求回滚公共合同来掩盖业务缺陷。

## 5. 重要文档与交接

本篇需补充旧模块 → Adapter → 资源的实际调用图、复用和改写清单、异常映射、工具授权范围、测试/真实 provider 证据以及禁用项。S04 消费固定的 Adapter 版本和事件合同；S06 再消费角色能力。当前实现/验证：**not_run**。
