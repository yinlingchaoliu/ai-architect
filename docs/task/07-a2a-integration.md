# S07 · A2A 通讯与互通验证

状态：planned。前置：S06。对应目标：L1、L5。依据：[A2A 技术方案](../ai-archtect/03-a2a-protocol.md)。规范基线沿用固定 A2A 1.0.1、线协议 1.0；不是对执行日最新版本的承诺。

## 1. 目标与阶段变化

从平台内本地调用扩展到独立 Agent 服务间调用。新增 A2A Server 对外提供逻辑 Agent，A2A Client Adapter 调用远端；本地 Agent 不绕 HTTP 自调用，MCP 继续只作为工具连接。

```text
外部 Client → A2A Server → Runtime → 本地 Agent / Workflow
本地 Workflow → Runtime → A2A Client Adapter → 独立远端 Agent
```

## 2. 实施任务

| ID | 工作 | 主要交付（拟） | 验证重点 |
|---|---|---|---|
| S07-A | 固定 SDK/Schema 与 binding | A2A Adapter 依赖锁、兼容矩阵 | SDK 真正支持目标协议；不混入 0.3 名称/字段 |
| S07-B | Card 与目录接入 | 生成/获取/缓存 Card，远端定义绑定 | skills、接口、认证、协议及端点资格校验 |
| S07-C | 入站服务 | Send/Stream/Get/List/Cancel/Subscribe | 映射 Runtime、认证去重、输入续答和工件 |
| S07-D | 出站 Adapter | ID/状态/上下文映射、原始回执 | Message-only 与 Task 不混淆，未知结果不造终态 |
| S07-E | 流恢复和取消 | 持久远端引用、查询对账、事件组装 | 断流/重启不盲目重发，取消确认和物理停止分开 |
| S07-F | 双向互通套件 | 独立进程、固定版本 SDK 参考对端 | 真实协议回执，不仅是平台自测同一序列化逻辑 |

## 3. 关键决定

HTTP+JSON/SSE 作为首版 binding，接口和 wire enum 以固定规范为准。平台 run_id/task_id 不冒充远端 contextId/taskId；每条映射包含远端身份、接口、认证主体和协议。声明的能力必须有实现和测试，首版不开 pushNotifications。

远端提交超时不等于未执行；有 task ID 先查询，无 ID 且无幂等保证时停止自动重发有副作用动作。入站持久去重，出站不假定对方必去重。工具/远端完成与本地输出合同/业务验收分别记录。

## 4. 验收与回滚

覆盖双向发现和调用、Task 查询/取消、Message-only、输入/认证等待、SSE 工件、重启恢复、错误版本、重复消息、认证失败和受限出站。特别注入“远端已执行、本地落库前断连”，观察真实副作用是否重复。

只运行 local fake 不足以完成本步骤；需要独立跨进程参考对端，但业务模型仍可 stub。回滚先禁止新的远端委派和入站创建，保留远端任务映射并对账在途动作；已有远端任务不能因禁用 Adapter 就标已停止。

## 5. 重要文档与交接

本文补齐精确 SDK/规范、Card、脱敏 wire 示例、状态/ID 映射、双方回执、失败重连与取消记录。S08 的控制权转交建立在此任务通讯之上；A2A 互通本身不等于 Handoff 完成。当前互通/实现：**not_run**。
