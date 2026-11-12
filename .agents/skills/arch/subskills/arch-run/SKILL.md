---
name: arch-run
description: 为已授权步骤维护 run 目录和思考、行动记录，绑定候选与脱敏证据，不以写日志冒充执行。
---

# 执行记录员

本文件是 arch 的内部子技能；按需读取，不要求创建独立进程或 Agent。

## 输入与职责

输入：已授权步骤计划、候选、实际命令/结果和当前授权。

产物：run 索引、判断依据、行动记录及证据索引。只处理本职责；共用格式和证据规则见 [文档合同](../../references/document-contract.md)。

## 处理方法

1. 只有用户要求实施或已有实施授权时执行代码/依赖/外部调用；仅要求设计时写计划。使用现有工程运行入口，不创建额外调度服务。
2. 每轮使用既有 run 或新编号，记录 HEAD/dirty、输入/锁/候选指纹、解释器、精确写集。保留执行前用户改动，不能从最新 HEAD 误推所有改动都是本轮。
3. 思考记录可观察的依据、取舍与决定；行动记录真实命令/时间/退出/产物/失败及修正。不要保存内部隐含推理、密钥、完整环境或带凭据的请求。
4. 阶段收尾交 arch-review 写 03-review，交 arch-reflect 写 04-reflection；更新 run 索引。未运行或不可见的费用/质量标 not_run/null，不补写成功。

## 模板与衔接

本职责内置模板：

- [actions](assets/templates/actions.md)
- [run-index](assets/templates/run-index.md)
- [thinking](assets/templates/thinking.md)

各类型的默认路径和组合见 [产物目录](../../assets/catalog.json)。填写后返回主入口，报告来源、输出路径、状态、未解决项和所需其他子技能。按 [语义审阅清单](../../references/semantic-review.md) 核对本职责，不以结构检查代替专业判断。
