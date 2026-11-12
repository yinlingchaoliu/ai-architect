# 复盘：LLM v2 设计交付与证明范围

日期：2026-11-12（Asia/Shanghai）。交付结论：**完整设计文档完成，self_review；实现 planned，待用户评审**。本轮未实现模型层、未安装新 provider 包、未调用真实模型、未压测或部署。

## 1. 产物

已交付 [总览](../README.md) 与 8 篇专题：源码借鉴、分层架构、公共合同、LangChain/provider、并发可靠性、配置生命周期、迁移接入、验收与决定。另有 5 份 Mermaid 图源及对应文档内图、Python Protocol/DTO 和 YAML 示例。本目录四类过程记录保持设计与实现状态分离。

架构主张为 Facade/ManagedChatModel → 单调用 kernel → provider adapter → LangChain/transport；Graph 拥有工具循环与图状态，Harness 拥有 Run/授权/上下文/总预算。注册和 prepared snapshot 借鉴 deepseek-harness，消息/模型协议优先复用 LangChain，没有拟建第二套业务调度器。

## 2. 实际输入与验证

- 当前项目 HEAD 为 98425ec；参考 deepseek-harness 为 47f9438，定向读取 LLM 及 agent-loop 消费边；[32 个源码输入指纹](evidence/sources.json) 区分项目、参考和已装框架，不声称逐行审计所有源码。
- 官方 LangChain、DeepSeek、HTTPX 资料已核对；langchain-deepseek 1.1.1 wheel 仅下载源码检查并核验 hash，未安装/执行该候选包。
- 一项 **零网络 payload probe** 使用当前 ChatOpenAI 与合成消息，证实 tool_calls 保留而 reasoning_content 未进入请求；[回执](evidence/langchain-payload-probe.json)。它不是新 provider 互通证明。
- 定向 `archkit.py check` 验证当前目录的链接、锚点、JSON 和模板完成度；另检查 YAML 标量类型/引用、Python 源码和 6 段 Markdown Python 示例 AST、5 份内嵌图与图源一致、已选源码未漂移、写集及密钥形态。最终结果见 [document-check.json](evidence/document-check.json)。
- 本轮环境未发现 mmdc，未做 Mermaid parser、SVG/PNG 渲染或视觉验收。图语义由本轮人工自审；不能把内嵌文本一致说成图语法/可读性已验证。

## 3. 语义自审结论

| 评审点 | 结论与限制 |
|---|---|
| 源码事实和目标分开 | 当前 Manager/SDK/Graph 行为有源码入口；所有新接口/部署图标为拟建 |
| 参考与差异 | 逐项列明 registry/PreparedCall/stream/retry 借鉴；usage/EOF/无限 retry/reasoning 回放不照搬 |
| Native LangChain 接入 | bind_tools/structured/cache/SDK retry/回调旁路均有约束；真正兼容仍需实施行为测试 |
| 高并发 | 区分 C/RPM/TPM、pool、队列 bytes、公平、背压和多副本；没有虚构 QPS 或生产容量 |
| 失败与终止 | 明确部分输出禁止透明重试、EOF incomplete、cancel、预算 pending 和远端未知生成 |
| 配置与权限 | revision 不可变、原子发布、secret/endpoint 配对、轮转/撤销；图 owner 显式切换 |
| 演进与回滚 | L0-L5 各有可运行切片/重要文档/验收；其他 task 不自动重排 |
| 证明边界 | 代码实现、协议回放、真实 provider、容量/生产均未验收；自审不等于独立审阅或用户接受 |

## 4. 并行变更与写集保护

设计期间工作区出现另一路依赖整理：原 requirements 子目录与部分子项目 requirements 被移除，根 requirements/若干安装说明等变化。已重新读取根声明，修正不再适用的“当前必须三环境”描述；没有恢复这些文件或修改其他 task。元数据观察只说明路径变动，不能证明变动原因/质量，见 [outside-observations.json](evidence/outside-observations.json)。

本轮写入全部位于 `docs/task/02-platform-contracts-and-skeleton/llmv2/`，[write-set.json](evidence/write-set.json) 列实际文档/示例/过程记录及 hash。旧 S02 llm 方案内容未读取或引用；.env/.env.local 未读取或变更。没有修改根依赖、实现代码、S02 概览或其他 task，也没有发消息、commit/push 或部署。

## 5. 下一消费者与未解决项

用户/实现负责人评审本方案后，可按 L0-L1 固定具体代码写集；生产账号额度/SLO、外层 BudgetPort 与身份来源、shared quota 部署及 thinking-tool replay 的真实验证还需补齐。本文给出解决合同和验收条件，未把它们写成已存在的能力。

本轮仅文档检查通过并完成自审，不自动开始实施。
