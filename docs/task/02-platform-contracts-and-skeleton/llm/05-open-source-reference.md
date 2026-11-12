# 05 · 主方案来源与采用决定

核验日期：2026-11-12（Asia/Shanghai）。版本：v0.2。采用关系已由用户明确：**DeepSeek Harness llm为主方案，Dify提供Provider/ModelType能力组织参考，LangChain负责本项目适配实现。** 本文不再并列比较多个网关作为本模块主架构。

## 1. DeepSeek Harness：主服务模式

参考本地仓库 `/Users/chentong/AI/PatientCare/github/deepseek-harness/packages/llm`，HEAD `47f943859bef60e4160492346772ded9b24f765a`。关键源码与hash见 [本轮输入](source-baseline.json) 和 [前轮分析](../run-01/00-analysis.md)。

| 已核对机制 | 本项目采用 | 平台化补充 |
|---|---|---|
| LlmRuntime / LlmAdapter稳定seam | ModelService + Provider/CapabilityAdapter，统一上层调用 | 扩展到六类能力，不复制TS/Cordis运行时 |
| 注册、dispose、先校验后replace | 原子发布与清理句柄，Provider目录/精确模型分开 | 多副本revision与撤销窗口显式定义 |
| prepareCall绑定registration/config、单次dispatch | PreparedCall固定模型/类型/能力/参数/版本/凭据引用 | 跨进程幂等和预算另由共享端口实现 |
| block/usage/finish流词汇、EOF和consumer清理 | 标准ModelEvent，LLM流式是一等合同 | 增加音频/转写事件；缺终态不默认成功 |
| replayState保留协议续答信息 | versioned continuation envelope | 增加tenant、协议和模型revision授权边界 |
| retry policy与token-meter独立 | 唯一有限重试owner，usage观察/上下文估计/费用分离 | 不采用无界always或把启发式估算当账单 |

源码定位：[服务/prepareCall](../../../../../deepseek-harness/packages/llm/llm/src/index.ts)、[共享类型](../../../../../deepseek-harness/packages/llm/llm/src/types.ts)、[直接适配](../../../../../deepseek-harness/packages/llm/llm-deepseek/src/adapter.ts)、[多厂商快照](../../../../../deepseek-harness/packages/llm/llm-pi-ai/src/adapter.ts)、[usage投影](../../../../../deepseek-harness/packages/llm/token-meter/src/usage-projection.ts)。参考TS测试只读，未在本轮运行；不以源码结构证明本项目吞吐或账务正确。

## 2. Dify：Provider 与 ModelType 能力组织

Dify官方规范将供应商声明、模型类型、特性和参数规则分开；Provider凭据和模型级配置也有各自边界。本项目据此定义ProviderDefinition/ProviderInstance与AIModelEntity，不直接依赖Dify进程或SDK类型。[官方Model Specs](https://docs.dify.ai/en/develop-plugin/features-and-specs/plugin-types/model-designing-rules)

具体核对了Dify Plugin SDK中ModelProvider的凭据验证、按ModelType列模型/取得模型实现，以及schema中的ModelType/AIModelEntity字段。六类能力取自本轮用户范围；当前核验SDK另含扩展枚举，并非本项目必须全量采用。[ModelProvider源码](https://raw.githubusercontent.com/langgenius/dify-plugin-sdks/8ae50c7a8d53915303ffb4fad0902e4114720ad8/src/dify_plugin/interfaces/model/provider.py)、[模型实体源码](https://raw.githubusercontent.com/langgenius/dify-plugin-sdks/8ae50c7a8d53915303ffb4fad0902e4114720ad8/src/dify_plugin/entities/model/schema.py)

Dify概念用于“有什么/要什么/能力边界”；不直接复用带请求计时可变状态的AIModel实例跨线程。其源码明确提示该类非线程安全，本项目改为每请求计时/collector与共享只读配置分离。[AIModel生命周期源码](https://raw.githubusercontent.com/langgenius/dify-plugin-sdks/8ae50c7a8d53915303ffb4fad0902e4114720ad8/src/dify_plugin/interfaces/model/ai_model.py)

## 3. LangChain：统一实现框架

LLM优先使用原生BaseChatModel及工具/结构化/流式能力；Embedding使用Embeddings的query/documents接口。对其他类型复用相应集成，缺统一接口时用薄的类型化async Runnable，不把六类硬塞成聊天模型。[模型接口](https://docs.langchain.com/oss/python/langchain/models)、[Embedding接口](https://docs.langchain.com/oss/python/integrations/embeddings)

本次安装源码基线为LangChain 1.5.0、core 1.8.0、langchain-openai 1.7.4、LangGraph 1.2.20，沿用S01实装，不在本轮更新包。前轮机制观察验证了默认async线程fallback、usage chunk相加、模型完成后Schema仍可失败；当前又定向读取Embedding/Compressor默认async与Embedding分批源码。它们是实现限制的输入，不是新模型服务已经测试通过。

平台公共DTO与Provider实体保持独立；LangChain原生对象在内部适配/Graph投影保真使用。薄Bridge不得建立另一套调用治理，避免两套重试、两笔usage、重复token输出。v3流/profile的beta边界保留在适配层，不成为跨平台公共wire Schema。

## 4. 当前项目反例输入

lib_request的现状提供了必须消除的反例：同类Embedding有SDK和requests两套实现，文本返回原JSON、视觉返回SDK Choice、相似度查询串行逐文档取向量；视觉HTTP实现又混用了Response解析。新设计不保留“不同能力对应不同厂商客户端”的上层方式。完整逐接口映射见 [06](06-project-integration.md)。

## 5. 后续扩展

**LiteLLM作为后续无感接入的优先选择：保持Provider外观、ModelType和上层调用合同不变，仅通过配置或内部实现替换接入。** 本版不为其划分本模块职责。

参考版本/文件hash、官方链接及本轮查证边界见 [reference-snapshot.json](reference-snapshot.json)。没有安装参考项目的新依赖、部署外部产品或运行收费模型。
