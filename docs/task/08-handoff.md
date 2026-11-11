# S08 · Handoff 控制权转交

状态：planned。前置：S07。对应目标：L3、L4。依据：[Handoff 设计](../ai-archtect/04-collaboration-patterns.md#4-handoff)。

## 1. 目标与模式语义

实现用户会话处理权从 A 转给 B，B 接续后续交互；不同于 Worker 完成子任务后把结果返回 A。先验证本地转交，再验证经 A2A 交给远端，始终使用同一平台 owner/epoch 规则。

```text
A 提议 → Runtime 验权/检查在途动作 → B 准入接受
       → 数据库 CAS owner/epoch → outbox 激活 B → B 接续用户
       → A 的旧 epoch 写入和派发失效
```

## 2. 实施任务

| ID | 工作 | 交付（拟） | 重点 |
|---|---|---|---|
| S08-A | HandoffIntent 与状态机 | `collaboration/handoff/`、handoffs 表 | proposed/preparing/accepted/committed/active 与拒绝/过期 |
| S08-B | 原子控制权更新 | Runtime ownership API | 唯一 handoff_id、CAS owner/epoch、幂等激活 |
| S08-C | 转交上下文 | context projection 与产物引用 | 目标、已完成、约束、未决项；不复制全部会话/密钥 |
| S08-D | 在途动作和故障恢复 | 等待/取消/对账、outbox | prepare 不执行业务，commit 后旧 owner 不复活 |
| S08-E | 转交边与限额 | Workflow allowed_edges/max_hops | 防循环、越权和无限转交 |
| S08-F | UI/API 接续语义 | 当前 owner 与转交事件 | 用户消息路由到提交后的有效 owner |

远程的 prepare/commit 是平台控制流程，不把它伪装成 A2A 标准原生握手。B 的准入阶段只检查能否接收，真正业务 A2A 请求在平台 commit 后发出；发送结果未知沿 S07 规则对账。

本地图的等待与续行复用 LangGraph interrupt/Command resume 和固定 checkpoint，类型化 context 注入已提交的 owner 视图；它们不替代数据库 CAS。MCP elicitation 和工具审批等中断必须作为可续行控制流保留，不触发普通工具重试；仅在业务策略确需时启用审批 middleware。

## 3. 验收与回滚

测试 B 拒收、prepare 超时、commit 前后崩溃、重复通知、A 的过期回传、B 激活失败和用户消息与转交并发。任何时刻仅一个有效处理 owner；已经发往外部的动作不能靠 epoch 自动撤销，冲突写域必须先排空/对账。

准备失败时 A 保持 owner；提交后通知失败由 outbox 重试激活，不让 A 恢复旧身份。需要回到 A 时走一次新的显式转交。回滚关闭新 Handoff 创建，按持久 owner 处理已有会话，不能简单恢复旧字段或删除转交记录。

## 4. 重要文档与交接

本文补齐实际状态/时序图、上下文合同、CAS 与外部副作用边界、并发故障记录、用户接续和回退结果。S09 继续复用 ownership/lease 基础，不把 Handoff owner 与 Swarm 所有参与者混为一谈。当前实现/验证：**not_run**。
