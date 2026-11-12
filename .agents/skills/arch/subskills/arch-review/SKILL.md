---
name: arch-review
description: 复核源码证据、图文契约、测试与真实调用，生成文档验证和执行复盘，明确证明边界。
---

# 架构与交付审阅者

本文件是 arch 的内部子技能；按需读取，不要求创建独立进程或 Agent。

## 输入与职责

输入：同一候选文档/源码、实际检查和运行回执。

产物：validation、验证 JSON、run 的 03-review。只处理本职责；共用格式和证据规则见 [文档合同](../../references/document-contract.md)。

## 处理方法

1. 先验证快照与候选字节仍匹配，再检查需求覆盖、调用事实、边界/依赖、失败和终止、图文一致、链接与模板填写。机械通过不能证明架构语义正确。
2. 按实际任务选择语法、渲染、导入、行为、集成、真实外部、恢复/生产验证，不为普通文档小改启动全部测试或外部付费调用。
3. 逐条绑定命令、环境、输入、实际结果、脱敏回执与限制。API 可用、fake 模型、本地真实协议、外部真实模型和生产效果分别报告；历史失败与最终结果可并存。
4. 交付前自审或有实际授权的独立审阅注明身份；没有独立审阅/用户接受就如实记录。只有必需实现、证据和文档齐备才标本步完成，不擅自重写其他 task。

## 模板与衔接

本职责内置模板：

- [review](assets/templates/review.md)
- [validation](assets/templates/validation.md)
- [verification](assets/templates/verification.json)

各类型的默认路径和组合见 [产物目录](../../assets/catalog.json)。填写后返回主入口，报告来源、输出路径、状态、未解决项和所需其他子技能。按 [语义审阅清单](../../references/semantic-review.md) 核对本职责，不以结构检查代替专业判断。
