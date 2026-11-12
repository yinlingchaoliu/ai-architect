# 本地工具与复用

`scripts/archkit.py` 仅依赖 Python 3.10+ 标准库。没有模型调用、联网、安装依赖或 shell 拼接；不会自动执行源码。命令从项目根运行时，前缀为 `python3 .agents/skills/arch/scripts/archkit.py`；从其他位置运行传技能脚本路径和显式 `--root`。日期以用户时区为准，可用 `--date YYYY-MM-DD` 覆盖宿主日期。

## 查目录与生成骨架

```bash
python3 .agents/skills/arch/scripts/archkit.py catalog
python3 .agents/skills/arch/scripts/archkit.py scaffold --root . --type architecture --dry-run
python3 .agents/skills/arch/scripts/archkit.py scaffold --root . --type step --step 02-platform-contracts --date 2026-11-12 --dry-run
python3 .agents/skills/arch/scripts/archkit.py scaffold --root . --type run --step 02-platform-contracts --run-id 01 --dry-run
```

去掉 `--dry-run` 才写文件。`architecture` 生成目标总览及分层文档；`step` 同时生成概览/索引/详细计划；`run` 生成索引和四篇记录，各模板分别归 run/review/reflect 所有。其他类型与路径在 [catalog.json](../assets/catalog.json)。所有结果是 draft，stdout 列待填变量；它不能替代读代码、选型或执行。

同一组输出在写入前检查冲突；任一文件已存在则整组拒绝，没有覆盖开关。项目已有文档时读取后定向编辑，而不是先删文件再套模板。默认识别已有 `docs/ai-archtect`，否则目标目录为 `docs/architecture`；可指定 `--architecture-dir docs/design --task-dir docs/migration --current-doc docs/as-is.md`。模块等专题用 `--name registry`；步骤名用 `01-example` 形式。输出路径和符号链接不能逃出 `--root`。

## 选择源码指纹并检查漂移

```bash
python3 .agents/skills/arch/scripts/archkit.py snapshot --root . --path server/app --path server/pyproject.toml --output docs/source-snapshot-run-01.json --dry-run
python3 .agents/skills/arch/scripts/archkit.py check --root . --path docs/design --snapshot docs/source-snapshot-run-01.json
```

按实际分析范围重复 `--path`。生成 snapshot 时同样需去掉 dry-run；输出必须是新文件。跳过常见依赖/执行缓存/本地技能、密钥文件、符号链接和超过 5 MiB 的文件，不复制源码内容或环境。结果记录 `hash_only`，内容已审阅与源码事实仍写进 source-audit；目录快照不代表已逐行审计目录。

`check` 检查本地文件链接/Markdown 锚点、JSON 语法、未填模板和可选快照漂移。仅检查明确选择的目录，历史备份和不属当前候选的旧验证报告不应混入。普通交付不带 `--allow-draft`；草稿试用可加该参数，忽略待填写变量，但不忽略缺失链接。它不核对外部 URL，也不判断架构正确性、业务接受或 Mermaid 语法。

## 图源与可选渲染

```bash
python3 .agents/skills/arch/scripts/archkit.py scaffold --root . --type diagram-sequence --name registry --dry-run
python3 .agents/skills/arch/scripts/archkit.py render --root . --source docs/design/diagrams/registry-sequence.mmd --output docs/design/diagrams/registry-sequence.svg
```

图源是带“示例”语义的模板，需替换成有来源的节点和边。render 使用已存在的 `mmdc`，可用 `--mmdc` 指定可执行文件；需浏览器配置时用项目内 `--puppeteer-config` JSON。内置 [mermaid-config.json](../assets/mermaid-config.json) 提供严格模式、字体后备和布局。未找到渲染器返回 not_run，不能据此声称图已经渲染。渲染成功也仍需视觉回读中文、箭头、裁切和可读性。

## 包检查与自测

```bash
python3 .agents/skills/arch/scripts/archkit.py package-check
python3 .agents/skills/arch/scripts/self_test.py
```

包检查核对注册子技能、模板拥有者、内部引用和完整性；模板中的输出链接在生成场景里核对。自测在临时空项目复制整包，检查实际生成、冲突时零写入、路径越界/符号链接拒绝、secret 排除、无 Git 使用和快照漂移。它证明脚本机制和可搬运性，不是独立模型评估。
