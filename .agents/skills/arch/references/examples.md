# 来源经验、使用示例与证明边界

## 本聊天流程如何转为通用能力

| 本项目实际产物/要求 | 本包抽象 | 没有固化的项目特例 |
|---|---|---|
| docs/current-architecture.md | source/current，源码事实与现状图 | 独立 Python 示例集合这一结论须重新读代码 |
| docs/ai-archtect | target/module/protocol/collaboration/flow | 六层、A2A/MCP 版本、技术选型不是全项目默认 |
| docs/task | roadmap，每阶段可运行切片与重要文档 | S01–S11 的数量和排期不是通用承诺 |
| docs/task/01-langchain-upgrade | step/technology，概览入口与详情目录 | 不写死框架/SDK/供应商和“最新”版本 |
| docs/task/01-langchain-upgrade/run-01 | run/review/reflect，四类记录与候选证据 | 现有测试数字不复制为未来真实结果 |
| 其他 task 改动前确认 | layout-and-changes，按用户当前保护范围处理 | 不把每个可逆写操作都新增审批 |
| 实际升级暴露冲突与新 API 差异 | technology/review，求解、运行与真实模型分别验证 | 不照搬旧 SDK 示例或凭 API 存在宣称采用 |

上表是溯源案例，**不是本包运行依赖**；迁移时不需要这些业务文件。模板、规范和 CLI 均在本目录内。

## 可直接使用的请求

- `$arch 阅读当前项目源码，在 docs 生成现状架构和主要业务调用流。` 路由 source → current/flow → diagram → review，只写要求的文档，不实施服务。
- `$arch 根据现状设计支持动态配置的运行平台，并给出分层、通讯和协作方式。` 选择 target、module、protocol、collaboration、technology；未知容量明确，方案默认 proposed。
- `$arch 把当前架构渐进迁移到目标架构，每一步提供重要文档，先处理我指定的依赖升级。` 选择 roadmap/step/technology，生成总览→步骤概览→详情的链接结构。
- `$arch 执行已批准的某一步，补齐 run-02 的思考、行动、复盘、反思；其他 task 改动前先确认。` 选择当前步骤专业能力与 run/review/reflect；执行边界沿用户授权，真实与替身结果分开。
- `$arch 只补一篇接口设计，不改其他文件。` 只加载 protocol/diagram/review，避免重新生成整个架构包。

## 本包验证的解释

结构/脚本自测证明文件闭合、模板分派和拒绝危险路径等机制；试用文档需再做语义自审。没有独立 Agent 盲测、真实模型效果或运行平台验收，就不宣称已经证明。完整历史测试回执在 validation-report.json。
