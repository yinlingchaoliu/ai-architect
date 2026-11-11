# S04 · 运行内核与持久化

状态：planned。前置：S03。对应目标：L4、L6。设计依据：[运行状态与可靠性](../ai-archtect/05-runtime-and-reliability.md)。

## 1. 目标与架构变化

将“API/CLI 内直接执行、内存保存结果”升级为“API 提交命令、Worker 推进持久任务”。这是平台成为统一执行者的步骤，先支持一个 Agent，不提前复制四套协作引擎。

```text
Run API → PostgreSQL（Run / Task / Attempt / outbox）
        → Worker 领取任务 → S03 Adapter → 进度/工件/观察
        ← 持久状态与事件 ←────────────────────────┘
```

## 2. 任务拆分

| ID | 工作 | 主要实现（拟） | 关键验证 |
|---|---|---|---|
| S04-A | 数据模型和迁移 | runs/tasks/attempts/events/artifacts/outbox/inbox | 状态版本、租户键、唯一约束、读写迁移兼容 |
| S04-B | Run/Task API 与事件查询 | `runtime/`、`api/` | 异步提交回执、状态/工件查询、SSE 断线补读 |
| S04-C | DB 队列、租约和容量预留 | Scheduler/Worker | SKIP LOCKED、owner_epoch、旧 Worker 提交拒绝 |
| S04-D | 幂等和副作用账本 | operation ledger、dispatch/inbox | 重复派发不重复受控动作；未知结果先对账 |
| S04-E | 取消、等待、超时和预算 | Run/Task/Attempt 控制 | 父子传播、释放等待槽、累计预算、物理停止观察 |
| S04-F | checkpoint 与恢复 | LangGraphAdapter、持久 saver | 固定版本、独立 namespace、重启查原执行再续行 |
| S04-G | 样例切到平台调度 | 已适配会议/单 Agent 用例 | 新入口成为唯一调度 owner，旧入口只作隔离对照 |

## 3. 关键决定

Runtime 是 Task/Attempt 状态唯一写入者。Pattern 只提交意图，Worker/远端只提交观察。业务动作具有稳定 operation_id；数据库状态和 outbox 同事务，消息采用可重复投递和持久去重。租约过期不能直接证明旧执行停止。

远端或工具调用超时后进入 reconciling，先检查回执和副作用，确认安全才重试。框架 checkpoint 保存计算状态，平台数据库保存目标、任务、归属和回执；禁止两者各自重试同一次业务动作。运行完成、输出 Schema 通过和业务接受分开记录。

## 4. 验收与回滚

必须做跨进程故障验证：领取后崩溃、工具已执行但落库前崩溃、重复投递、租约过期后旧 Worker 回传、流连接中断、取消期间子进程继续运行、恢复时旧制品不兼容。结果应可从 DB、工件和真实副作用回读。

单 Agent 需完整通过创建 → 运行 → 产物 → 查询；等待输入、明确失败、取消和未知结果均有对应路径。新内核不能延续 Manus “失败也计为 completed”的判断。

回滚先停止新派发，排空或取消并对账；保留新库和事件，不做破坏性 downgrade。只有确认无冲突在途动作，才把隔离的新请求转回旧入口，不能让旧入口接着重复消费新队列。

## 5. 重要文档与交接

本文补齐数据模型/状态图、事务边界、恢复顺序、注入故障点与回执、迁移/回滚演练和已知限制。S05 消费稳定 Run manifest、任务接口和租约实现；S06 消费调度/依赖/事件能力。当前实现和故障实验：**not_run**。
