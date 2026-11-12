# 项目架构技能

项目内提供 `arch`，入口为 [.agents/skills/arch/SKILL.md](.agents/skills/arch/SKILL.md)。用户调用 `$arch`，或任务需要从源码生成架构、分层、业务流、迁移拆解与执行文档时，按需读取该入口和相关子技能。技能规范与模板全部在该目录中，不依赖其他项目的文档库。

本项目文档沿用 `docs/current-architecture.md`、`docs/ai-archtect/`、`docs/task/`。这些是业务输入与历史产物，事实须与当前源码/基线核对。步骤细节进入 `docs/task/<步骤名>/`，执行记录进入其 `run-XX/`；其他 task 只链接步骤概览，再由概览链接细节。用户要求变更其他 task 方案前确认时先取得该项确认，不借本步工作批量改写它们。

技能生成的骨架为 draft，需填充源码和实际证据后审阅。写集、实现权限和外部调用范围以用户当前指令为准。
