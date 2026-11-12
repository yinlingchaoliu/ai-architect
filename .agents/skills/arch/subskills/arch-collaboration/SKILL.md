---
name: arch-collaboration
description: 设计 Orchestrator-worker、Supervisor、Handoff、Swarm 的控制权、状态流、策略契约和收敛。
---

# 多智能体协作架构师

本文件是 arch 的内部子技能；按需读取，不要求创建独立进程或 Agent。

## 输入与职责

输入：业务任务、参与能力、运行内核和权限/预算约束。

产物：模式比较、各模式流程、统一策略契约。只处理本职责；共用格式和证据规则见 [文档合同](../../references/document-contract.md)。

## 处理方法

1. Orchestrator-worker：主控拆解任务、依赖/并行执行、聚合；Supervisor：每轮根据观察选择调用、审阅、返工或结束。分别写决定输入与合法输出。
2. Handoff：后续交互控制权转给接收方，不自动回原 Agent；写接受/拒收、owner/epoch、原子转交与在途动作。Swarm：参与者自主提案/认领/审阅，有共享协调和收敛，不等同一次 gather。
3. 共用任务/状态/事件/恢复内核，策略提交类型化意图，适配器执行；避免每个模式各自持久化和争抢同一业务控制权。
4. 每种采用的模式写上下文传递、输出合同、重复执行防护、失败/取消、有界停止和模式组合边界。未要求全部四种时只展开有关模式。

## 模板与衔接

本职责内置模板：

- [collaboration-design](assets/templates/collaboration-design.md)

各类型的默认路径和组合见 [产物目录](../../assets/catalog.json)。填写后返回主入口，报告来源、输出路径、状态、未解决项和所需其他子技能。按 [语义审阅清单](../../references/semantic-review.md) 核对本职责，不以结构检查代替专业判断。
