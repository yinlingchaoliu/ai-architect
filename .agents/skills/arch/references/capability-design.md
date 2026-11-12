# 能力拆分与职责选择

## 先按文档需要识别专业判断

| 问题 | 主要职责 | 协作 |
|---|---|---|
| 代码实际怎样连、旧文档是否过期 | source / current | diagram、flow |
| 为什么这样分层、怎样组织代码和部署 | target | module、technology |
| 每个模块的数据/状态/接口归谁 | module | protocol、flow |
| 一次业务如何完成，哪里等待/失败 | flow | diagram、module |
| 跨服务/框架如何互通 | protocol | technology、review |
| 多 Agent 谁决定、谁执行、谁持有控制权 | collaboration | module、flow |
| 稳定版本/新 API 如何采用与退出 | technology | step、review |
| 怎么分阶段迁移并保留可运行切片 | roadmap / step | target、technology |
| 实施发生了什么、结果是否够 | run / review / reflect | 当前步骤专业职责 |

角色是专业检查视角，不自动成为平台 Agent、组织任命或独立子进程。一个人/当前 Agent 可依次消费多个子技能。服务、前端、数据、算法、安全与运维的专项规则按实际边界选用；不因使用某语言或提到某术语就新增空角色。

## 新增子技能的条件与最小内容

当新文档具有现有能力不能表达的判断、输入输出或验收，并且本轮允许扩展项目技能时，物理创建 `subskills/arch-<name>/SKILL.md`，写明适用场景、输入、职责、方法、验收和衔接。配本地模板，在 catalog.json 登记拥有者和输出路径，在主入口增加一行路由。简单格式变化给原职责增模板即可，不拆出只有转发作用的子技能。

模板必须随技能携带；不能只写“沿用某项目旧文档”。新术语、外部规范版本和工具依赖按需本次核验；通用规则不固化当前供应商、层数、版本和绝对目录。扩展后运行 package-check、官方 quick_validate，并用有代表性的输入试用；测试输出放临时目录，说明自审/独立审阅及未覆盖项。
