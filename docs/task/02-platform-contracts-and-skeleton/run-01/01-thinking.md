# 思考：判断依据与方案取舍

日期：2026-11-12。本文件记录可观察依据、技术判断和权衡，不记录模型隐含推理。

## 已固定的约束

用户确定框架为LangChain，要求阅读参考仓库并先评审优化；正式llm目录暂不修改。本轮只写run-01，不执行平台改造、依赖升级或付费模型请求。当前实装版本已核对，参考仓库保持只读。

## 对前轮设计的重新判断

前轮将独立ModelClient、通用Driver和LangChain Bridge组合，隔离意图合理；但若Driver默认直接操作SDK、自己拆SSE，再经Bridge还原AIMessageChunk，就会重复框架已有能力。源自“将来可能换框架”的额外通用性，不应在已明确LangChain的主路径上持续付出转换和维护成本。这里识别的是结构性成本/风险，尚没有证明实际延迟节省多少。

比较三条候选：

| 路线 | 优点 | 代价/风险 | 判断 |
|---|---|---|---|
| A 自有通用协议驱动 + Bridge | 框架隔离最强 | SSE、内容块、工具、replay、usage重复维护，可能双重组装 | 特殊协议兜底，不作默认 |
| B GovernedChatModel 包裹所有native model | 每条路径统一BaseChatModel入口 | bind_tools可能返回Runnable；结构化输出/stream/callback需要完整透明代理，容易双span/双事件；同步fallback会落线程池 | 仅必要适配，不先写通用重代理 |
| C 原生LangChain内部调用 + 统一InvocationCoordinator + 两类受控入口 | 复用生态和异步流；业务边界仍稳定 | 需明确middleware顺序、usage采集和防旁路；仍要真实互通验证 | **推荐候选** |

C不是两套治理：Agent由ModelAccessMiddleware进入，独立业务由ModelClient facade进入，二者调用同一协调器/预算authority/registry。框架handler仍执行原生模型调用，不绕成“middleware→ModelClient→同一Agent”。

## 为什么不能只加一个middleware

当前安装源码的agent handler会先调用模型，再做结构化输出处理；外层handler报错时，模型可能已完成且有费用。离线探针验证了这一点。因此middleware管理授权、尝试和最终化，request-scoped UsageObservationCollector在原生模型回调边界采集usage，账本仍由协调器唯一写入。回调不是另一套计费系统，缺回执时继续pending。

同样，最靠近模型的治理wrapper必须位于所有请求改写之后；否则授权/预留基于旧消息或旧模型，而发送用了新模型。首期不允许下游middleware替换模型或偷偷多次handler；需要重试的唯一owner每次重新准备独立ModelAttempt。

## 性能与通用性的取舍

先消除重复模型实例/连接、同步fallback、重复转换、重复usage和逐token重操作，再考虑独立网关或语言重写。保留外部wire DTO和插件合同，把内部LangChain类型视为所选框架的执行合同；不让框架对象进入租户/余额领域，也不让厂商字段进入业务策略。

原生异步、连接复用、有界排队和多副本治理仍需同时具备。LangChain的max_concurrency或InMemoryRateLimiter并不提供跨副本TPM和货币预算；不能因为采用框架就删除平台治理。

## 待用户确认

建议确认C路线、PreparedInvocation生命周期、LangChain-native backend plugin、单一usage事实归一及单一retry owner。确认后再按候选变更清单调整正式llm文档；当前没有把推荐直接写成已接受决定。
