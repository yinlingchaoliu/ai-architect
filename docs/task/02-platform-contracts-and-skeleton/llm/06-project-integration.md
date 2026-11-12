# 06 · lib_request 统一封装与当前项目接入

日期：2026-11-12。版本：v0.2。状态：拟迁移设计；本轮没有修改lib_request、业务入口或依赖。lib_request的14个核心Python文件及消费点已定向回读，输入hash见 [source-baseline.json](source-baseline.json)。

## 1. 当前问题的源码依据

| 当前实现 | 已核对事实 | 需要的新行为 |
|---|---|---|
| [req_call.OpenAIAssistantClient](../../../../lib_request/src/lib_request/req_call.py) | 同步requests，返回response.text，无统一ModelResult/usage/显式超时 | LLMRequest统一返回LLMOutput，标准错误/截止/计量 |
| [openai_text2vec.OpenAIEmbeddingClient](../../../../lib_request/src/lib_request/openai_text2vec.py) / [ReqEmbeddingClient](../../../../lib_request/src/lib_request/req_text2vec.py) | 同一能力有SDK和HTTP两条路径，前者可选model，后者硬编码；均返回List[float] | EmbeddingRequest批量/query统一，模型由entity决定，保留维度/索引身份与usage |
| [OpenAIVisionClient](../../../../lib_request/src/lib_request/openai_vision.py) | 构造器保存model，但两个调用仍硬编码gpt-4o；返回Choice | vision作为LLM image feature，返回同一LLMOutput；model_ref必须真正生效 |
| [ReqVisionClient](../../../../lib_request/src/lib_request/req_vision.py) | dict经data发送却声明JSON，之后对requests.Response访问choices | 修正协议/响应混用；不能保留这条错误路径当兼容标准 |
| [DeepSeekEmbeddingClient](../../../../lib_request/src/lib_request/req_text2vec_deep.py) | 已deprecated，但向chat/completions找embedding字段，仍公开导出 | 不用聊天模型伪造Embedding；无对应类型配置则发送前明确拒绝 |
| [DeepSeekModelListClient](../../../../lib_request/src/lib_request/req_model_list.py) | 返回/models原始JSON字符串，不含可信ModelType/特性Schema | Provider发现候选→校验发布→list_models返回AIModelEntity |
| [SimilaritySearchBase](../../../../lib_request/src/lib_request/sim_search.py) / 两个SimSearch子类 | 每次query一请求，再逐文档串行请求Embedding；cosine计算与厂商Client耦合 | retrieval helper只消费统一Embedding能力；文档离线批量索引，在线query独立 |
| [count_token](../../../../lib_request/src/lib_request/count_token.py) / [包导出](../../../../lib_request/src/lib_request/__init__.py) | 导入时创建OpenAI client，固定GPT-4 tokenizer；包入口急切导入全部模块 | 无key可import，按需装配集成；token估算显式模型/来源，不充当真实账单 |
| [根main.py](../../../../main.py) | 消费多个不同Client与get_embedding/request/model_list等方法 | 迁移到同一ModelClient.ainvoke/astream，用不同Request表达能力 |

这些是静态源码事实，不是本轮真实接口实验。S01已做部分依赖/SDK兼容测试，但没有证明上述所有业务行为正确；不能把import测试当六类模型服务验收。

## 2. 目标包：在 lib_request 中收敛统一封装

保留用户已使用的包路径`lib_request`，将其规划为统一模型能力包。平台bootstrap负责装配Provider配置、可信context和治理ports，避免另建第三套模型SDK。

```text
lib_request/src/lib_request/                 # 以下为拟目录
  __init__.py                               # 轻量公开合同/客户端；无client/网络副作用
  contracts/
    model_type.py / provider.py / model_entity.py
    requests.py / results.py / events.py / errors.py / context.py
  client.py                                 # async ModelClient与只读context view
  service/
    model_service.py / registry.py / prepare.py / invocation_runner.py
    ports.py                                # Secret / Budget / Admission / Ledger等抽象
  providers/                                # Provider定义/实例配置Schema和模型声明
  adapters/langchain/
    llm.py / embeddings.py / rerank.py / speech2text.py / moderation.py / tts.py
    observation.py / continuation.py
  bridges/
    chat_model.py / embeddings.py            # LangChain consumer投影，同一执行内核
  compat/                                   # 原类名/同步接口过渡，不能自建厂商调用
  transports/                               # 明确装配的异步连接与远程ModelClient

platform/src/agent_platform/
  contracts/models/                         # 引用同一份纯合同，不复制另一套DTO
  bootstrap/model_resources.py              # 装配lib_request.ModelService
  infrastructure/model_resources/           # 共享预算/配置/密钥/限流/账本port实现
```

lib_request/contracts逻辑上是共享模型合同，不包含L5实现依赖；platform的领域/合同消费纯类型时不能触发LangChain、OpenAI或环境key初始化。lib_request不能反向import平台Run/Task实体，只接收稳定ID、可信context和注入ports，避免循环依赖。

打包时可分client/contracts基础依赖与LangChain/厂商集成extras，保持remote client或纯合同使用者不必加载全部厂商；具体包/锁在实施时求解。当前lib_request的Hello SDK README和metadata需要随实际迁移重写，本轮不改源码或发布包。

## 3. 旧接口到统一请求的映射

| 旧入口 | 新入口 | 兼容约束 |
|---|---|---|
| OpenAIAssistantClient.request(text) | ainvoke(LLMRequest(messages=...)) | 新业务取result.output.text，不再解析provider JSON |
| OpenAIEmbeddingClient.get_embedding / ReqEmbeddingClient.get_embedding | ainvoke(EmbeddingRequest(texts=[text], purpose=...)) | 旧Facade可取vectors[0]；模型/维度/usage仍由新服务固定 |
| vision_image_path / vision_image_url | 媒体入口生成ImageBlock引用，再ainvoke(LLMRequest(...)) | model_ref + vision feature校验；不返回SDK Choice |
| model_list | list_models(model_type=...) / Provider管理发现 | 列表是标准实体，不承诺原始JSON结构永久兼容 |
| DeepSeekEmbeddingClient.get_embedding | 解析EmbeddingBinding，缺配置明确Unsupported | 不再尝试chat endpoint；迁移调用者，不假返回None成功 |
| SimSearchReq / SimSearchOpenAI | RetrievalService注入同一个Embedding client | 批文档向量+本地检索不混同RERANK |
| count_tokens(text) | 显式TokenEstimator(model_ref, content) | 标local_estimate/未知，禁止当provider usage |

过渡Facade只做参数/输出投影，全部委托ModelService。若必须阶段兼容request()返回str，可输出明确的LegacyPayload白名单；不能编造provider request ID/usage来凑旧形状。SDK Choice等厂商对象不承诺无损兼容，必须盘点实际消费者并迁移。已错误的HTTP视觉实现不保留为“兼容功能”。

同步Facade使用受控SyncModelClient生命周期和单独loop/池，见 [08](08-model-types-and-api.md)。禁止把一套requests类与一套SDK类同时保留为两个发送owner。新代码不再新增厂商命名的Client。

## 4. 当前Agent / RAG / 服务接入

| 消费者 | 拟接入点 | 责任保持 |
|---|---|---|
| lib_graph.build_agent / agentmcp.run_query | bootstrap注入PlatformChatModel；框架工具循环继续原生执行 | 不在Bridge重试/计费，不把MCP塞进模型Adapter |
| graph_discussion BaseAgent | 过渡Facade或async桥接；异常改显式错误 | 旧“失败文本仍继续讨论”在迁移时记录行为变化 |
| Manus LLMManager | 以ModelClient替换SDK发送，content/tool_calls投影保留 | 原float/默认0累计费用退为只读视图，账本唯一 |
| 旅行/讨论/MCP router | 同一ModelClient/Bridge，统一deadline/retry/context | 会话和调用请求隔离，SDK多重重试退出 |
| LangServe | 可跨独立环境的远程ModelClient/Bridge | 沿用S01依赖隔离事实，不能强装冲突extra |
| PDF/CSV/向量库 | PlatformChatModel + PlatformEmbeddings分别装配 | 不将DeepSeek文本默认值覆盖Embedding provider；SQL/检索仍归原边界 |

## 5. 渐进实施候选与重要文档

| 切片 | 对应既定步骤 | 拟写集/重要文档 | 必须取得的证明 |
|---|---|---|---|
| M0 本轮正式重写 | 当前设计 | 本llm目录及run-01/rewrite-01记录 | 方向与用户要求一致；源码保持原字节，本轮不写其他task（范围外变化单列） |
| M1 纯合同和注册骨架 | S02 | lib_request/contracts、service ports/registry/prepare、fake各类型Adapter、platform装配骨架；接口Schema文档 | 六类Schema/错误/注册、默认值隔离、单次派发，无key可import |
| M2 LLM和视觉理解 | S03 | LangChain LLM adapter/bridge、lib_request旧文本/视觉Facade；接入指南 | 同一LLMRequest文本/图像/工具/流/Schema；具名provider真实测试另留证 |
| M3 Embedding及第二Provider | S03 | Embedding adapter/bridge、目录实体、显式BatchPlan、旧embedding消费者 | query/document、顺序/维度/索引身份、批usage及替换合同；其他能力不能假通过 |
| M4 Rerank/语音/审核逐项接入 | S03能力扩展切片 | 类型Adapter、配置/计量fixture；每能力独立重要说明 | 已声明能力分别通过；未实现类型显式unsupported |
| M5 持久治理与多副本 | S04 | Budget/Admission/Ledger ports实现、恢复/取消/对账报告 | 竞态、重复、发送后崩溃、缺usage、租户隔离、Redis/DB故障 |
| M6 存量批迁移与容量 | 既定S10及已就绪治理 | 旧入口/文档/测试改造、压测/灰度/回滚报告 | 已迁移集合无SDK旁路，不以单能力通过称全仓统一 |

以上只在专题内细化接入候选，不修改S02根概览或S03/S04/S10计划。若需调整其他task范围/依赖，另提交具体修改确认。用户本轮授权重写设计，没有授权实现全部包或做付费多厂商实验。

## 6. 灰度与回滚

按tenant/ModelType/别名逐项灰度，先对比规范化请求与fake/本地协议fixture；真实双发需单独额度且分别记账。一个逻辑call只有一个实际发送owner，不能旧SDK和新服务同时发。

回滚只切新请求active binding，旧PreparedCall/在途请求继续用原版本并最终化。已发送unknown不切旧入口重发，不删除usage/账本或改历史价格。新功能类型尚无旧兼容路径时明确不可用，不回落成聊天猜测结果。业务数据/索引变更单独迁移，尤其Embedding更换不能只改模型名。

旧正式设计备份保存在 [重写前归档](../run-01/rewrite-01/evidence/llm-before.tar.gz)，这是文档回溯，不是生产回滚证明。
