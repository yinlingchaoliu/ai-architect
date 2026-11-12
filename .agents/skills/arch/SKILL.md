---
name: arch
description: 从项目源码生成现状架构、目标分层、业务流和接口设计，逐步拆解迁移任务，并维护步骤执行、验证与复盘文档。适用于架构分析与工程改造规划。
metadata:
  version: "1.0.0"
---

# Arch 架构专家

以源码和用户目标为输入，交付能追溯、能评审、能逐步实施的架构文档。本入口负责判断范围、组合子技能和核对交付；具体文档规则、专业细节与模板由各子技能拥有。全部规范和模板随本目录携带，不要求其他项目提供外部规范库。

## 工作方式

1. 先确认实际仓库、目标、允许写入范围和已有文档；读取 [共用文档合同](references/document-contract.md) 与 [目录及变更规则](references/layout-and-changes.md)。依当前请求选择设计、补充单文档或实施记录，已有授权继续使用。
2. 新项目/旧基线过期时先由 arch-source 取证；仅改一个已确认模块时定向回读。选下面所需子技能，只加载这些 SKILL.md 和模板，避免每次通读全部。
3. 文档形成后由 arch-review 按范围检查来源、语义、图文和证明边界。向用户交付主要入口、变更与实际验证；尚未执行的部分单列。

## 子技能与产物

| 子技能 | 专业职责 | 使用时机 |
|---|---|---|
| [arch-source](subskills/arch-source/SKILL.md) | 源码分析师 | 源码分析、模块/边事实、选取文件指纹 |
| [arch-current](subskills/arch-current/SKILL.md) | 现状架构师 | 当前架构、入口表、差距与图源 |
| [arch-target](subskills/arch-target/SKILL.md) | 系统架构师 | 目标总览、分层、目录建议、关键决定 |
| [arch-module](subskills/arch-module/SKILL.md) | 模块架构师 | 模块详细设计与契约、必要数据/状态图 |
| [arch-flow](subskills/arch-flow/SKILL.md) | 业务流程分析师 | 业务流文档、时序与状态转换 |
| [arch-protocol](subskills/arch-protocol/SKILL.md) | 接口与协议架构师 | 接口表、消息/状态/ID 映射、互通验收 |
| [arch-collaboration](subskills/arch-collaboration/SKILL.md) | 多智能体协作架构师 | 模式比较、各模式流程、统一策略契约 |
| [arch-technology](subskills/arch-technology/SKILL.md) | 技术选型与依赖专家 | 技术特性基线、兼容矩阵、采用与退出决定 |
| [arch-roadmap](subskills/arch-roadmap/SKILL.md) | 迁移与工程规划师 | 总计划、步骤依赖图、重要文档与验收映射 |
| [arch-step](subskills/arch-step/SKILL.md) | 步骤方案设计师 | 步骤入口、plan、指南、回滚及子任务合同 |
| [arch-run](subskills/arch-run/SKILL.md) | 执行记录员 | run 索引、判断依据、行动记录及证据索引 |
| [arch-review](subskills/arch-review/SKILL.md) | 架构与交付审阅者 | validation、验证 JSON、run 的 03-review |
| [arch-reflect](subskills/arch-reflect/SKILL.md) | 过程反思与改进者 | run 的 04-reflection 或独立反思文档 |
| [arch-diagram](subskills/arch-diagram/SKILL.md) | 架构图与流程图设计师 | Mermaid 图源、可选 SVG/PNG、图例及渲染记录 |

一次请求可以组合多个子技能；子技能是本包内部可按需读取的专业指令，不要求启动独立 Agent。若实际需要额外 Agent、工具或外部服务，沿当前会话授权和可用能力处理，不把技能加载当成执行权限。

## 模板与本地工具

模板按产物类型分别内置；[catalog.json](assets/catalog.json) 映射每种类型的拥有者、模板和默认输出路径。`python3 scripts/archkit.py catalog` 从本技能目录运行可列出目录。实际项目根目录显式传给命令；脚本不调用模型或联网，不覆盖已有文件。

```bash
# 在仓库根目录使用
python3 .agents/skills/arch/scripts/archkit.py catalog
python3 .agents/skills/arch/scripts/archkit.py scaffold --root . --type current --dry-run
python3 .agents/skills/arch/scripts/archkit.py scaffold --root . --type step --step 02-platform-contracts --dry-run
```

骨架始终是 draft，须回读源码并填写。命令、变量、快照、校验及可选渲染说明在 [工具用法](references/cli.md)。复制本目录到另一项目的 `.agents/skills/arch` 后即可沿同一入口使用；不复制用户密钥、环境或本项目业务文档。

## 扩展与项目约束

现有子技能不能覆盖的新文档类型，先检查是否有不同的输入、专业判断、产物与验收。确需扩展且本次允许修改项目技能时，按 [能力拆分规则](references/capability-design.md) 新建子技能和模板并更新目录，不能把专题长文堆回主入口。

用户只要求架构设计时不实施升级或部署；执行任务时维护对应 run。其他 task 的方案或状态改动按用户当前约束取得必要确认，细节保留在本步目录。版本、协议和当前特性使用本次官方核验；不从参考案例固化“最新版本”或供应商。

基于本聊天的需求映射与可调用示例见 [案例与边界](references/examples.md)。包结构检查与实际验证记录见 [验证记录](references/validation-report.json)；结构通过不代替内容语义审阅。
