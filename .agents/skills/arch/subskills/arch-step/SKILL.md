---
name: arch-step
description: 细化一个迁移步骤，生成概览入口、详细计划、安装说明与回滚文档，保护其他 task。
---

# 步骤方案设计师

本文件是 arch 的内部子技能；按需读取，不要求创建独立进程或 Agent。

## 输入与职责

输入：步骤入口、前置产物、当前源码与技术基线。

产物：步骤入口、plan、指南、回滚及子任务合同。只处理本职责；共用格式和证据规则见 [文档合同](../../references/document-contract.md)。

## 处理方法

1. 读取本步实际输入与前置验收，固定目标、范围、读写集、接口、实施动作、失败/停止条件和交付文档；只细化当前步骤。
2. 步骤概览保留目标/状态/细节入口；技术讨论和变更写入同名目录，不能在 docs/task 根散落基线文档。其他步骤只链接概览，概览再链接细节。
3. 用户要求先确认其他 task 调整时，先完成当前范围并准备具体修改清单；取得该调整授权后才写入其他 task。不要因发现过期链接或状态就自动扩写方案。
4. 安装指南基于实际环境/锁；回滚明确触发、保留证据、旧源码/配置/制品和数据恢复、在途对账、回退验证及不能恢复的限制。没有实演就标 not_run。

## 模板与衔接

本职责内置模板：

- [installation-guide](assets/templates/installation-guide.md)
- [rollback](assets/templates/rollback.md)
- [step-entry](assets/templates/step-entry.md)
- [step-index](assets/templates/step-index.md)
- [step-plan](assets/templates/step-plan.md)

各类型的默认路径和组合见 [产物目录](../../assets/catalog.json)。填写后返回主入口，报告来源、输出路径、状态、未解决项和所需其他子技能。按 [语义审阅清单](../../references/semantic-review.md) 核对本职责，不以结构检查代替专业判断。
