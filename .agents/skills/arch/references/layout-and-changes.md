# 目录与渐进式披露

优先沿用用户指定和仓库既有目录。本包默认现状 `docs/current-architecture.md`，目标 `docs/architecture/`，计划 `docs/task/`。若项目已有 `docs/ai-archtect/`，沿用其拼写；不要在未要求时重命名。命令可显式覆盖架构目录、任务目录和现状文档路径，均限制在项目内。

```text
docs/
  current-architecture.md
  architecture/                 # 或项目已有的目标方案目录
    README.md                   # 总览和专题入口
    01-target-architecture.md
    modules/…                   # 需要时创建
    flows/…
    validation.md
  task/
    README.md                   # 顺序、依赖和步骤概览链接
    01-example.md               # 本步目标、状态、细节入口
    01-example/
      README.md
      plan.md                   # 本步详细方案
      technology-baseline.md    # 必要的依赖/特性细节
      upgrade-guide.md          # 实施需要时创建
      rollback.md
      run-01/
        README.md
        01-thinking.md
        02-actions.md
        03-review.md
        04-reflection.md
        evidence/…              # 真实回执产生后写入
```

其他 task 文档链接 `01-example.md`，该概览再接入本步目录。详细讨论、决定、基线和执行记录均进入对应步骤目录，不散落到 task 根。步骤入口之外只修改本轮已授权的文件；用户要求修改其他 task 前先确认时遵守该边界，不能以修链接/同步状态为由自行批量写入。

遇到旧总计划仍写 planned、子步骤已有完成回执，先核验差异，记录“历史总计划/当前步骤证据”并提交具体协调建议；不覆盖用户保护的其他文件。新建计划可以一次生成一致结构；已有计划按实际授权渐进修改。

run 编号沿用当前执行，不为普通状态询问或补记另开执行。思考记依据与取舍，行动记真实动作，复盘记结果与证明限制，反思记改进条件；日志是记录层，不另建执行控制器。
