# S01 回滚与兼容例外

对应 [run-01 结论](run-01/03-review.md)。本轮未变更业务数据库、部署或生产服务。

## 1. 回滚条件与顺序

当必需入口出现依赖、导入、消息合同或工具协议回归时，停止使用对应升级候选入口，保留失败回执，再恢复本轮变更的源码和声明。不要把旧包覆盖安装到三个新环境中。需要旧依赖时新建独立环境，并先确认旧声明本身可求解。

1. 通过 [起始基线](run-01/evidence/baseline.json) 和最终 `write-set.json` 核对本轮变更；不使用 `git reset --hard` 或整仓覆盖，以免覆盖用户在执行前已有的文档改动。
2. 从 [source-before.tar.gz](run-01/backups/source-before.tar.gz) 取出确需恢复的文件，先在临时目录验证 hash，再逐个恢复。新增运行代码、测试、requirements 组仅在确认属于本轮写集后删除；保留执行证据。
3. 两个 MCP `.python-version` 的原内容和来源单独保存在 [python-versions-before.json](run-01/backups/python-versions-before.json)。`.env.local` 是独立本地私密配置，未归档，不由源码回滚覆盖；两份受控 `.env` 已保持改造前内容。
4. 关闭本轮启动的进程后切回已确认的旧环境。三个新环境均在仓库外；回滚源码不要求删除它们，也不改变其他项目环境。
5. 重跑旧行为基线。原 `graph_discussion` 的精确 requirements 存在 core/graph 版本冲突，见 [旧组求解失败证据](run-01/evidence/old-graph-resolution.log)。**未宣称旧依赖可直接重建或旧运行环境已验证恢复。**

## 2. 实际演练范围

对初始归档的 **228 个文件**，在临时副本中用候选文件覆盖后再恢复原字节，逐个与起始 SHA-256 对照通过，见 [rollback-check.json](run-01/evidence/rollback-check.json)。两个解释器文件另存原文及 hash。演练没有覆盖工作区，没有重新安装旧环境，也不是生产回滚证明。

## 3. 保留的兼容边界

| 项目 | 本轮处理 | 后续边界 |
|---|---|---|
| LangServe | 与 MCP 2 的 SSE 依赖隔离，保留独立进程；当前 LC/core/provider 不降级 | S02/S04 再按平台服务职责处理，不提前改写其方案 |
| classic/community/experimental | 仅保留旧检索和 SQL 消费；SQL 只读连接 | 按既有 S10 逐模块退出旧业务编排；本轮不代写其他 task |
| MCPAdapter / v3 events | 精确锁定并验证；运行时 beta/experimental 警告保留 | 在资源/事件适配边界演进，不把上游 beta 当成稳定契约 |
| 内存 checkpoint | 已验证 pause/resume、恢复前无副作用、恢复后执行一次 | S04 才验证持久数据库、进程重启、跨线程隔离和副作用对账 |
| 旧讨论/Manus/旅行流程 | 修复导入、日志目录、状态声明及 SDK 消费所需问题 | 业务失败状态、累计预算、全局 pool 的平台化留在后续 task |
| 原 LlamaIndex 样例 | 独立旧栈，未纳入本轮 LangChain 执行环境 | 单独迁移前保持独立，不能安装进已验证组 |

以上兼容例外和运行方式只记在 S01 目录。若因此需要调整其他 task 的方案，先向用户提交具体改动并取得确认。
