---
name: arch-diagram
description: 按实际语义生成架构、依赖、时序、状态和数据图，维护 Mermaid 图源与可选渲染。
---

# 架构图与流程图设计师

本文件是 arch 的内部子技能；按需读取，不要求创建独立进程或 Agent。

## 输入与职责

输入：已审查的组件/边、状态转换或数据关系，以及事实/拟建标签。

产物：Mermaid 图源、可选 SVG/PNG、图例及渲染记录。只处理本职责；共用格式和证据规则见 [文档合同](../../references/document-contract.md)。

## 处理方法

1. 先写节点/边/图例表再选择图种：组件/层次用 flowchart，跨边界交互用 sequenceDiagram，生命周期用 stateDiagram-v2，数据关系用 erDiagram；不强行混图。
2. 节点 ID 使用简短 ASCII，中文显示名加引号；分组反映职责，控制长标签和交叉线。逻辑层不伪装部署单元；实线/虚线必须解释事实、控制、数据或拟建语义。
3. 核心图保留 .mmd，文档可嵌入 Mermaid；用户需要可读图片时使用可用渲染器生成 SVG/PNG，回读中文、箭头、裁切和可读性。未渲染/未查看则明确标注。
4. 使用本子技能 assets 的图源和内置 mermaid-config.json 起步，逐条替换为有来源的真实节点/边；不能把模板节点当项目事实。没有 mmdc 时不暗装全局依赖，交付图源并记录 render_not_run。

## 模板与衔接

本职责内置模板：

- [architecture](assets/templates/architecture.mmd)
- [data](assets/templates/data.mmd)
- [dependency](assets/templates/dependency.mmd)
- [sequence](assets/templates/sequence.mmd)
- [state](assets/templates/state.mmd)

各类型的默认路径和组合见 [产物目录](../../assets/catalog.json)。填写后返回主入口，报告来源、输出路径、状态、未解决项和所需其他子技能。按 [语义审阅清单](../../references/semantic-review.md) 核对本职责，不以结构检查代替专业判断。

## 模板预览

[架构模板 PNG](assets/previews/architecture.png)、[时序模板 PNG](assets/previews/sequence.png) 展示模板的中文与边界标记；五类图的 SVG 同目录保存。预览是通用示例，不是目标项目的架构事实。
