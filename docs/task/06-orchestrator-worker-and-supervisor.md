# S06 · Orchestrator-worker 与 Supervisor

状态：planned。前置：S05。对应目标：L3。设计依据：[四种协作方式](../ai-archtect/04-collaboration-patterns.md)。

## 1. 目标与改造顺序

先在同一 Runtime 上实现两种集中决策模式，用现有会议讨论和旅行规划形成可比较的交付。先拆明确的任务/产物边界，再改协作策略，不另建消息总线或状态库。

```text
Orchestrator-worker：目标 → 计划/DAG → Workers → 依赖屏障 → 聚合/审阅
Supervisor：目标 → 观察/决策 → 专家或并发组 → 观察/重做/结束
```

## 2. 任务拆分

| ID | 工作 | 实施范围（拟） | 验收 |
|---|---|---|---|
| S06-A | 固定 Pattern 意图和决策合同 | `collaboration/base`、contracts | Schedule/Review/Wait/Finish 不可越权 |
| S06-B | Orchestrator-worker | 对应 Pattern、DAG 校验、join、聚合 | 依赖无环、必需/可选任务失败策略、受控并行 |
| S06-C | Supervisor | 决策 Schema、修订/委派/停止 | 每轮返回监督者；非法动作被拒，循环和费用有界 |
| S06-D | 会议角色迁移 | 分析师、主持人、三专家、总结者 | 角色经 Registry 发现，产物和追问可追踪 |
| S06-E | 旅行规划迁移 | 现有领域 Agent、依赖和输出 | execution_sequence 真正生效，依赖未满足不运行 |
| S06-F | 同条件评测 | 固定用例、模型/工具 profile、预算 | 单 Agent/旧图/两种模式质量、延迟和成本可比较 |

## 3. 两种模式的重要区别

Orchestrator 主要围绕子任务图分解和聚合，计划修订有版本并明确失效下游；Supervisor 主要围绕每轮观察作下一步决策，可委派、审阅、重做或等待。两者都保留各自 Pattern owner，Worker 返回结果，不接管用户会话。

模型提出的计划和决策先由 Runtime 校验依赖、目标白名单、预算和当前授权。旧会议图未实际接入的追问需要显式实现和测试，不能通过文案声称已经支持。专家输出必须有 Schema 与来源标记，模拟工具输出不能充当真实研究证据。

专家/监督者由 create_agent + middleware 构建，决策通过 response_format/structured_response 获取；自定义拓扑使用 StateGraph/子图，并通过 v3 事件观察进展。当前模型 profile 决定 ProviderStrategy/ToolStrategy，禁止退回自由文本关键词解析。1.5 的 ModelRouterMiddleware/auto mode 作为 beta 验证项，路由只允许选择本 Run 已固定并获准的模型候选，记录实际选择和费用；失败时切到具名静态路由配置。[当前特性基线](01-langchain-upgrade.md)

## 4. 验收与回滚

Orchestrator 测试三独立任务并行、下游依赖屏障、必需失败、可选降级、聚合不合格和有界重做。Supervisor 测试发现缺口后再委派、相同决策无进展、非法 Agent、最大修订数和预算停止。两种模式都需通过 Worker 重启、重复事件和取消路径。

仅 Future 返回或 max_rounds 到达不计成功。业务质量与成本在固定条件下报告，无真实模型则只交本地机制验证。回滚按 Workflow revision 关闭新模式，新请求回单 Agent/旧整图 Adapter；在途 Run 沿固定版本排空，对账后再迁移。

## 5. 重要文档与交接

本文补齐两张实际模式图、决策 Schema、角色/依赖映射、计划与产物样例、回归和同条件评测、业务语义差异。S07 消费稳定的委派/事件接口，不直接改两种 Pattern。当前实现/评测：**not_run**。
