# 04 · LangChain 封装的性能、多用户并发与可靠性

日期：2026-11-12。版本：v0.2。状态：设计；真实吞吐、p95、内存上限、节省比例均UNKNOWN。本轮未做压测，不从架构图推出高并发已实现。

## 1. 服务共享，请求状态隔离

ModelService/Registry是进程级服务；Provider配置和adapter/model/HTTP资源可在同revision内复用。tenant、会话历史、tools、参数、计时、取消、collector与预算授权按请求隔离。for_context是只读Facade，不修改共享服务current_user或默认模型。

从Dify借鉴Provider/ModelType概念，不照搬其带可变计时字段的AIModel实例跨线程共享。LangChain BaseMessage/profile也非天然深度不可变：请求变换采用copy-on-write，持久/API边界detach一次；业务不得修改全局模型headers/tools/callback列表。

## 2. 原生异步与能力映射

| 能力 | LangChain实现优先级 | 性能/正确性验收 |
|---|---|---|
| LLM | 原生BaseChatModel.ainvoke/astream | 具体integration实现native async，stream/usage/取消可验证 |
| TEXT_EMBEDDING | Embeddings.aembed_query/aembed_documents | 验证override而非默认executor；显式batch、usage与分块语义 |
| RERANK | 可用的专用rerank/compressor集成，或类型化async Runnable | 保留score/id，acompress默认线程fallback不能当native async |
| STT/TTS/MODERATION | 可用集成或薄async Runnable能力实现 | 不假设有统一BaseChatModel，不能把同步SDK套async函数就称异步 |

当前安装core 1.8.0的BaseChatModel、Embeddings和Compressor默认异步可能委托executor；provider 1.7.4的部分集成有native async。方法名存在不足以证明无阻塞。上轮离线探针只验证了机制，不能替代具体六类integration的测试。

同步lib_request兼容放在明确的SyncModelClient边界：专用后台loop与其连接池、受限提交队列、截止/关闭生命周期；高并发API一律走async。禁止在运行中的event loop里阻塞future.result/requests/invoke或asyncio.run；AsyncClient和异步数据库池不能跨loop复用；可共享不可变合同/配置，loop所属资源与服务执行实例分别装配。

## 3. 连接、模型工厂和配置快照

池key包含provider instance/租户凭据域、endpoint、协议、credential version、transport和model config revision；获准共享平台账户才可跨用户复用连接。冷启动采用per-key singleflight，避免突发请求重复建client；锁只包创建，不等待推理。

模型/工具Schema/参数规则按revision缓存。新revision发布后新调用创建/取新handle，在途使用原handle；旧handle引用归零再关闭。不要每请求new OpenAI/ChatOpenAI，也不要每token重新查目录或获取secret。credential轮换必须与endpoint快照同代，不能先await key再读另一份active配置。

prepare_call固定语义请求和能力边界，一次消费；取消信号不deep-freeze。LangChain框架tools/response_format绑定可能增加实际Schema，需记录并核对发送样例及预算上界，不调用私有factory函数来掩盖绑定差异。

## 4. 薄桥接与一套流语义

对外遵循DeepSeek式ModelService/StreamChunk语义，适配器内部复用LangChain原生对象和SDK parser；不重复实现每家SSE。Graph桥接只选择native projection，通过同一ModelService执行内核转发原生chunk，避免“chunk→JSON→chunk”的逐token往返。普通API/UI需要标准ModelEvent时在出口投影一次。

流内最终消息组装由一个明确所有者完成：优先复用LangChain已有组装结果/结束回调，核心只投影必要结果，不默认运行第二个全量BlockAssembler。若某集成需要自有组装，只在该适配器内启用并验收内存/终态，不能与native累加并行重复。

桥接嵌套span标记logical_call/provider_attempt；UI只消费一个模型token通道，成本只按物理attempt归并。不能同时把原生callback和外层stream事件都渲染为两份token。bind_tools及结构化输出必须仍经过同一服务内核；Bridge不得直接delegate一个未治理的native runnable给上层。

非流式与流式共享生命周期和类型规则，不强制全部请求always-stream。LLM可走原生ainvoke；需要增量时走astream。框架可能因callbacks/运行上下文自动启用stream，应按实际入口核验。Embeddings/Rerank等不支持stream就明确拒绝，不伪造单块“流式成功”。

## 5. usage 观察与批处理

LLM使用request-scoped async observer采集模型结束/partial；Schema失败发生在模型成功之后时仍保留费用事实。observer不是账本owner，回调/trace采样失败不能把费用变成0；协调器检查缺证并保留pending。

其他能力由adapter报告usage/receipt，不依赖LLM回调。Embedding集成可能内部tokenize、分块、平均或发多个HTTP：服务必须有显式BatchPlan/physical request观察。首个严格预算profile关闭隐藏重试与未登记的自动拆分，按供应商限制预分批，并核对实际请求数；不满足可观测性时不声称费用完整。长文本分块/索引策略由RAG显式处理，不偷偷改变向量语义。

大批任务有输入数量、字符/token、返回向量维度和总bytes限制；并发批按per-call及provider上限，不用无限gather。避免查询时逐文档重新请求embedding：文档索引在入库时批处理/持久，在线查询只生成query向量后检索；cosine排序是retrieval职责。

## 6. 多用户准入、公平性与预算

按tenant/user/Run/ModelType/共享provider account/replica分别限额，账号下多key不能被当独立满配额。local Semaphore仅限制本机；多副本使用共享admission authority。LangChain max_concurrency只约束局部batch，InMemoryRateLimiter不覆盖跨进程、TPM或货币预算。

短队列按租户做有界加权公平候选，设置per-user/per-tenant/总队列上限，deadline包括排队/预算检查/重试。队列满返回OVERLOADED，不能无限create_task。本地公平+共享配额不等于全局严格公平，后者需要按quota group分片的准入owner/实测等待界限。

Redis脚本多key原子性要求同slot；首期用单authority或明确分片，同一上限不能散落多个不相关counter。DB/共享limiter不可用时新付费派发fail-closed。配额permit与PG预留不是一个分布式事务，采用短许可、事务截止、发送前复核和明确补偿；不持DB锁等HTTP。

预算hold/permit lease到期不能证明远端已停。失联进入suspect/unknown，对账后安全回收；不能为提高并发而先释放未知费用或认定zombie请求不存在。

## 7. 有限重试、超时和取消

Provider给出策略，InvocationRunner是唯一执行者。SDK retries=0；Graph middleware、Runnable.with_retry等不重复重试同次模型调用。只在明确允许的代码、总deadline、尝试数和预算内重试；不启用无界always。请求准备、排队、连接、首字节、idle、总deadline和媒体写入分别有边界。

| 场景 | 默认处理 |
|---|---|
| 明确未发送的连接失败 | 有界backoff，保留未发送证据，重新检查预算/撤销 |
| 本地额度/队列拒绝 | 不污染provider全局健康，不切模型绕过用户额度 |
| 上游429/明确可重试错误 | 遵守Retry-After，按账户/部署冷却，单独记录尝试 |
| 发送后超时/重置 | unknown默认不重发；允许重复推理也需保留旧hold及额外额度 |
| 已可见内容后流失败 | 保留partial并失败，不拼接另一模型续文伪装同一结果 |
| Schema/权限/类型/拒答 | 不作传输重试；内容修正是上层显式新调用且计费 |
| consumer退出/取消 | 停止新尝试、关闭iterator/连接，记录本地与远端停止观察，费用另对账 |

API事件观察连接断开不等于Agent取消；模型consumer退出则关闭本次生成。TTS/STT还要清理流与媒体写入临时工件。服务滚动发布先停新准入再排空，不把旧unknown call切回旧SDK重发。

## 8. 内存、缓存与观测

输入媒体/消息、工具Schema、向量批量/维度、每块和总输出、stream buffer均设bytes/数量上限。音频/图像走受控对象引用，不能全量base64复制到日志/队列。轻量async callback只提取所需观察，不逐token同步落库或打印完整prompt/vector/音频。

流出口有界buffer与小窗口文本合并，保持tool/usage/finish顺序；慢消费者背压/超时，不无限积压。语义缓存/通用响应缓存首期不启用；后续按tenant/授权、model/type/revision、参数与输入指纹隔离。供应商prompt cache仍正常记录，不与应用响应缓存混为一谈。

遥测与费用记录分开：trace可采样并记录drop，必要dispatch/usage/账本事实不能随采样丢弃。指标采用低基数type/model/provider/status，tenant/user/Run ID放受控trace查询，避免基数膨胀。token/s、requests/s、音频秒、向量数和钱不混成一个吞吐值。

## 9. 容量验证候选

尚未取得实际机器/SLO/供应商配额，本方案只给实验口径。先50，再200，再500个在途请求，分别测LLM长短流、Embedding批量、音频慢消费和租户热点；idle SSE连接不算活跃模型请求。

同一拓扑对比原生integration与服务封装，记录新增延迟、TTFT、CPU/线程、峰值内存、连接/排队、公平性和usage完整率。固定tracing、媒体/文本大小、token分布、模型/配置版本、网络和并发。不把前轮三个机制probe当性能数据，也不承诺未经测量的TPS或优化百分比。
