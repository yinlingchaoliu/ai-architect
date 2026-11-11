# S01 · LangChain / LangGraph 升级

状态：**completed（S01 兼容切片，自审通过）**。日期：2026-11-12。LangChain 1.5.0 / LangGraph 1.2.20 已在隔离环境中安装，31 项回归和用户指定 deepseek-flash 的 4 项真实检查通过。S02 尚未执行。

本目录承载本步骤全部方案补充、执行记录和结论。[01-langchain-upgrade.md](../01-langchain-upgrade.md) 是供其他 task 引用的唯一概览入口；其他 task 的方案内容变更须先经用户确认。

- [详细方案与验收条件](plan.md)
- [特性采用基线与 S01 实测程度](langchain-feature-baseline.md)
- [安装、配置与使用指南](upgrade-guide.md)
- [回滚和兼容例外](rollback.md)
- [run-01：思考、行动、复盘、反思](run-01/README.md)

完整证据、已知上游警告和未验证范围见 [复盘](run-01/03-review.md)。不把本轮升级视为多智能体平台已完成或生产验收通过。
