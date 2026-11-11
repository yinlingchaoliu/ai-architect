# 架构图维护

当前架构源文件：[current-architecture.mmd](current-architecture.mmd)。目标架构源文件：[platform-architecture.mmd](../ai-archtect/diagrams/platform-architecture.mmd)。SVG 便于放大，PNG 用于通用图片预览，Markdown 中其余 Mermaid 代码块直接呈现细节流程。

本次使用 `@mermaid-js/mermaid-cli@12.2.0` 渲染，两幅图共用 [mermaid-config.json](mermaid-config.json)。需要 Node.js 和可用的 Chromium；这是文档工具，与业务 Python 环境无关。图中文字使用系统中文字体，SVG 未内嵌字体。

在仓库根目录、有可用 Chromium 的环境中，可使用已安装的 `mmdc` 重新生成：

```sh
mmdc -i docs/diagrams/current-architecture.mmd -o docs/diagrams/current-architecture.svg -c docs/diagrams/mermaid-config.json --no-font-embed
mmdc -i docs/diagrams/current-architecture.mmd -o docs/diagrams/current-architecture.png -c docs/diagrams/mermaid-config.json
mmdc -i docs/ai-archtect/diagrams/platform-architecture.mmd -o docs/ai-archtect/diagrams/platform-architecture.svg -c docs/diagrams/mermaid-config.json --no-font-embed
mmdc -i docs/ai-archtect/diagrams/platform-architecture.mmd -o docs/ai-archtect/diagrams/platform-architecture.png -c docs/diagrams/mermaid-config.json
```

如使用系统 Chrome，通过 `-p <puppeteer-config.json>` 指定 `executablePath`。渲染所有内嵌图可对 Markdown 输入运行 mmdc，输出放在临时目录；不需要把临时图或下载的工具依赖提交到仓库。
