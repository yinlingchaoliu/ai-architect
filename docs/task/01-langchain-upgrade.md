# S01 · LangChain / LangGraph 升级

状态：**completed（S01 兼容切片，self_review）**。2026-11-12 已完成 LangChain 1.5.0 / LangGraph 1.2.20 升级，31 项回归及 deepseek-flash 的 4 项真实检查通过。本文件是 S01 的渐进式披露入口，其他 task 只链接到本文件；具体方案、讨论变更和执行证据统一保存在 `docs/task/01-langchain-upgrade/`。

## 1. 本步目标与范围

先升级到本次核验的最新稳定 LangChain/LangGraph 组合，采用 create_agent、middleware、结构化输出、标准内容块、类型化事件和内置 MCP，验证现有主要入口。只执行 S01；不创建 S02 平台或改写其他 task 方案。

## 2. 详细方案与执行

- [完整升级方案与验收条件](01-langchain-upgrade/plan.md)
- [步骤目录](01-langchain-upgrade/README.md)
- [run-01：思考、行动、复盘、反思及证据](01-langchain-upgrade/run-01/README.md)

## 3. 必须采用和验证的能力

create_agent、middleware、结构化输出、content blocks、Runtime/context、v3 事件、内置 MCP、StateGraph/子图，以及分阶段的 checkpoint/interrupt 和模型路由。

详细版本、beta 边界和各阶段验证要求见[当前特性采用基线](01-langchain-upgrade/langchain-feature-baseline.md#3-必须采用和验证的能力)。本文件不复制全部特性明细；实际执行结果以 run-01 为准。
