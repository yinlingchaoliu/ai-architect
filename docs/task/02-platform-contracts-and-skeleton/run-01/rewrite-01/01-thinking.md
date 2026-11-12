# 思考：以已确认主方案收敛设计

用户本轮已经决定主次关系，工作目标是重写正式专题。前轮“LangChain原生内部路径+middleware协调”的比较只提供性能/兼容输入，不替代DeepSeek的稳定服务契约。无需再次请求是否采用DeepSeek。

## 判断与设计结果

| 输入/问题 | 可核实依据 | 本轮决定 |
|---|---|---|
| 多种lib_request调用/返回互不一致 | 请求文本原JSON、SDK Choice、向量list及两套HTTP/SDK入口 | 同一个ModelClient.ainvoke/astream，类型化Request和ModelResult |
| DeepSeek架构为什么适合主方案 | Runtime/Adapter、prepareCall、单次handle、配置捕获、流/replay/计量分离 | ModelService成为服务入口；Python实现复用LangChain，不复制TS/Cordis |
| 一个模型提供多能力如何理解 | Dify Provider、ModelType、AIModelEntity | Provider可公布多能力模型；具体模型逐类型/特性发布，不能要求一个聊天模型兼任向量和语音 |
| 通用性是否意味着全部messages/str | Embedding/重排/转写/审核/TTS输入输出不同 | 统一生命周期、方法和封套，保留六类强类型payload |
| LangChain要放在哪里 | LLM/Embeddings有接口，其他能力需专用集成或typed async Runnable | 实现框架在CapabilityAdapter内；Graph/向量库走薄Bridge，仍经同一内核 |
| 额外封装会不会逐token双重搬运 | 旧机制probe、框架chunk/组装源码 | 受控native projection与一次公共投影；一个assembler owner和一份usage |
| 共享模型与多用户并发是否冲突 | Dify AIModel可变计时；LC基类async可能executor | 共享只读模型/连接配置，请求状态独立；按具体integration验证native async |
| 六类能否都靠LLM callback计费 | Embeddings公开返回vectors，内部可拆批 | 每能力声明receipt源，真实物理请求逐attempt，缺证pending/null，多量纲计价 |
| 旧包是否另建第三模型SDK | lib_request已有消费者，平台需纯合同/装配边界 | 在lib_request收敛合同/服务/适配，bootstrap注入治理ports；包导入无副作用 |

后续透明接入产品仅保留一句扩展方向，不参与本模块职责图、调用链或验收owner划分。能力扩展依赖已安装受审适配器和配置发布，不接受用户上传执行代码。

## 取舍与限制

DSH服务语义与LC原生执行并存，需要薄桥接、参数映射和兼容fixture；不能靠命名成BaseChatModel就宣称透明。首次六类定义不是首次六类实装；按S02合同、S03逐能力接入、S04持久治理推进，本文不更改其他task。

高并发来自请求隔离、原生async、池/配置复用、有界排队/背压和共享准入，最终仍受厂商额度与实测环境约束。不能为了“简洁”去掉费用/未知边界，也不能为了“通用”复制完整网关或运行内核。
