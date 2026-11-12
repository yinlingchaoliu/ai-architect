# S02 · 统一模型服务设计

日期：2026-11-12（Asia/Shanghai）。版本：**v0.2，按用户确认方向重写**。设计取向已确定：**DeepSeek Harness llm 服务模式为主方案，LangChain 为实现框架，Provider + ModelType 组织多能力，统一上层调用。** 实现/部署/新能力验证均为 not_run。

本目录名沿用 llm，模块职责扩展为统一模型访问：LLM、TEXT_EMBEDDING、RERANK、SPEECH2TEXT、MODERATION、TTS。一个Provider可以提供多类模型能力；不要求同一个具体模型支持全部能力。图像理解属于LLM的vision特性，不再暴露另一套VisionClient调用协议。

## 1. 主方案

继承DeepSeek Harness的关键结构：稳定服务seam、Provider/Adapter注册、精确模型元信息、prepareCall绑定一次调用、配置快照、标准流事件、协议回放数据、独立重试策略与用量观察。实现适配器时优先复用LangChain，避免每家厂商各写requests、SDK封装和SSE解析。

统一调用只保留两种常用形式，以下为**拟API，不是已存在代码**：

```python
models = model_service.for_context(trusted_context)  # 每请求只读视图

answer = await models.ainvoke(LLMRequest(
    model_ref="chat.general@r1",
    messages=[Message.user("请概括需求")],
))
print(answer.output.text)

vectors = await models.ainvoke(EmbeddingRequest(
    model_ref="embedding.knowledge@r1",
    texts=["需求A", "需求B"],
    purpose="document",
))
print(vectors.output.vectors)

async for event in models.astream(LLMRequest(
    model_ref="chat.general@r1",
    messages=[Message.user("说明架构")],
)):
    consume(event)
```

请求类自动给出ModelType，上层不传API Key、base URL或厂商SDK对象；返回统一ModelResult，output按能力强类型区分。模型可显式选择，也可使用按ModelType发布的租户默认值；不存在默认配置时明确报错，不能把聊天模型当作全部能力的默认模型。

## 2. 目录与评审顺序

| 文档 | 内容 |
|---|---|
| [01 架构与主调用链](01-architecture.md) | DeepSeek主服务契约、职责、生命周期、LangChain适配与部署 |
| [02 Provider、实体、配置与公共合同](02-contracts-and-configuration.md) | Provider定义/实例、AIModelEntity、PreparedCall、注册发布、错误和流 |
| [08 六类能力与统一API](08-model-types-and-api.md) | 六类输入/输出、易用调用样例、特性/参数规则、文件与批处理 |
| [03 用量、预算与计费](03-usage-and-billing.md) | tokens/字符/时长/请求等单位、未知用量、预留结算、去重与对账 |
| [04 性能、并发与可靠性](04-concurrency-and-reliability.md) | 原生异步、模型/连接复用、薄桥接、有界队列、多用户与取消 |
| [05 参考来源与采用决定](05-open-source-reference.md) | DeepSeek主方案、Dify能力分层、LangChain实现边界与源码依据 |
| [06 lib_request与项目迁移](06-project-integration.md) | 现有核心源码的问题、逐接口映射、拟目录、阶段和回滚 |
| [07 验收与实际审阅](07-acceptance-and-review.md) | 需求覆盖、正反例、多能力/并发/费用/框架互通及未验证项 |

## 3. 已确定的设计规则

1. 一个ModelService拥有准备、派发与最终化；ModelClient是上层视图。LangChain/旧接口的Bridge只做类型投影，不另起调度、重试或记账。
2. Provider回答“有什么”，ModelType回答“要哪类能力”，AIModelEntity说明具体模型能做什么及参数边界；CapabilityAdapter负责如何执行。
3. LLM与其他能力共享调用生命周期、错误、身份、配置、费用框架；保留不同能力的真实输入/输出，不强行都变成messages和字符串。
4. ModelService是跨用户服务，可共享只读模型配置与传输资源；历史、tools、tenant、取消、计时和计量状态按请求隔离。
5. S02交付合同/骨架，S03逐能力接入，S04完成持久预算和跨副本治理；本轮不改写其他task范围或提前宣称其能力完成。

正式重写记录、旧稿备份、差异和实际文档检查见 [run-01/rewrite-01](../run-01/rewrite-01/README.md)。前轮run-01中“正式llm保持不变”的回执为历史研究阶段快照；本轮已获得重写授权，不覆盖旧证据。框架机制观察仍可回读，不能当作当前拟实现已通过。
