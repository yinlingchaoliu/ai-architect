# 分析：deepseek-harness 的 llm 对 ModelProvider 的启发

日期：2026-11-12。性质：源码事实 + 有条件的设计推论。参考根目录 `/Users/chentong/AI/PatientCare/github/deepseek-harness/packages/llm`，HEAD 与选定23份源码/测试指纹见 [基线](evidence/baseline.json)。本次聚焦五个产品包的主调用路径及关键测试，不声称通读全仓或完成安全/性能审计。

## 1. 真实职责划分

| 包 | 源码实际职责 | 对本项目的启发 |
|---|---|---|
| llm | LlmRuntime 注册路由、模型元信息、prepareCall、流拦截；共享 Message/StreamChunk/BlockAssembler | 核心 seam 应稳定、足够小；把提供方实现和调用方隔离 |
| llm-deepseek | 直接 fetch、序列化、SSE framing/translation、信号/idle timeout、usage 映射 | 特殊协议适配只在厂商边界；不让业务模型调用代码承担协议细节 |
| llm-pi-ai | 在同一 seam 后复用多厂商库，捕获配置快照、处理能力与 replay metadata | 精确协议薄适配和多厂商集成库可以共存，核心接口无需随厂商数量增长 |
| llm-retry | 消费 agent/request-error 扩展点；按提供方策略记录重试再等待 | 策略定义与执行分开、等待可取消；不能让每个 SDK/框架层自行重试 |
| token-meter | 会话日志的纯投影、usage/上下文压力/估算，按 Session 隔离 | usage、上下文占用、成本预算分别建模；重放统计应可复算 |

这些边界由实际 src 与测试支持。README 只用于定位，下面结论以实现为准。

## 2. 值得吸收的源码机制

### 2.1 小接口和双适配路径

[LlmAdapter](../../../../../deepseek-harness/packages/llm/llm/src/index.ts#L180) 将 `stream()` 设为唯一必需方法，目录/能力查询有默认实现。DeepSeek 精确协议与 pi-ai 多厂商适配都实现它。**启发**：厂商变化应止于 backend plugin，平台无需自建所有 SDK；当前项目可以用 LangChain model integrations 扮演多厂商适配库，特殊情况保留薄插件。

### 2.2 注册替换先校验、再提交

[registerAdapter / prepareRoutes / commitRoutes](../../../../../deepseek-harness/packages/llm/llm/src/index.ts#L338) 在候选全部合法后同步替换路由，不先清空再重建；disposer 防止已销毁注册再次 replace。[拓扑测试](../../../../../deepseek-harness/packages/llm/llm/tests/topology.spec.ts#L79) 检查通知时注册表已可读。

**启发**：模型配置采用不可变 revision 和原子发布；新请求用新版本，在途请求继续旧快照。注意这是单进程同步区的原子性，不能据此推导多副本发布/全局撤销已完成。

### 2.3 准备调用与实际派发绑定

[prepareCall](../../../../../deepseek-harness/packages/llm/llm/src/index.ts#L779) 捕获 registration、解析 config/context、校验派发配置一致，并以闭包限制一次派发。[服务测试](../../../../../deepseek-harness/packages/llm/llm/tests/service.spec.ts#L827) 覆盖单次调用和配置漂移。

[DeepSeek.stream](../../../../../deepseek-harness/packages/llm/llm-deepseek/src/adapter.ts#L214) 一次捕获 connection 并从该快照解析 key；[PiAiAdapter.current/stream](../../../../../deepseek-harness/packages/llm/llm-pi-ai/src/adapter.ts#L199) 对未变 profile 复用集合，配置变化生成新集合，并在 await 之前捕获本次集合。

**启发**：增补 PreparedInvocation，固定 model/capability/price/policy/credential version/backend instance。不能仅“先查模型名，发送时再找最新模型”。但原源码的 prepared handle 是进程内一次性闭包，不等于持久幂等；registration 绑定、每次 stream 的配置捕获，也不能不经验证就合称跨全部 revision 的事务快照。平台需要把这些边界显式串成一个准备对象。

### 2.4 精确模型能力与展示目录分开

[resolveModelInfo / resolveCallConfig](../../../../../deepseek-harness/packages/llm/llm/src/index.ts#L619) 验证精确 provider/model 的 context、默认输出与 reasoning；catalog 是建议目录，不替代请求校验。Pi-ai 拒绝不支持的 stop 和 reasoning，不静默 clamp。

**启发**：区分模型发现、配置发布、当前可调用模型；未知能力、明确不支持、已验证支持分别记录。多用户平台还需额外检查租户授权，不照搬 advisory catalog 的开放调用规则。

### 2.5 回放数据有协议归属

[forAdapter](../../../../../deepseek-harness/packages/llm/llm/src/index.ts#L823) 只向拥有历史路由和目标路由的同一适配器实例保留 replayState；[PiAiReplayState](../../../../../deepseek-harness/packages/llm/llm-pi-ai/src/replay.ts#L21) 保存 API、模型、response ID 与 thinking/text/tool signatures 等必要元数据。

**启发**：LangChain 的 additional_kwargs、response metadata、签名和 continuation 不能在转 DTO 时清空。跨模型/厂商不自动复用；平台需要 tenant/协议/模型 revision 绑定，适配器实例相同本身不是多租户授权证明。

### 2.6 流式边界和停止机制

[SSE parser](../../../../../deepseek-harness/packages/llm/llm-deepseek/src/sse.ts#L23) 委托标准 framing，EOF 无 DONE 抛 STREAM_CLOSED；[translate](../../../../../deepseek-harness/packages/llm/llm-deepseek/src/translate.ts#L86) 将最终 block、usage、finish 有序收尾；[adapterStream](../../../../../deepseek-harness/packages/llm/llm/src/index.ts#L847) 只把适配器边界错误转 finish，不吞 consumer/middleware 错误。两个适配器在 consumer 退出时 abort 并清理 iterator。

**启发**：必须区分 provider 失败、结构化校验失败、插件错误、consumer 关闭与取消。采用 LangChain 后复用其原生流和 SDK 清理路径，用针对性测试核对 EOF/取消，不再为每个 provider 默认写一遍 SSE parser。

### 2.7 usage 是事实，重放统计是投影

[DeepSeek.mapUsage](../../../../../deepseek-harness/packages/llm/llm-deepseek/src/translate.ts#L53) 将缓存命中从 prompt 总量中拆出；[tokenUsageProjection](../../../../../deepseek-harness/packages/llm/token-meter/src/usage-projection.ts#L107) 对同 step 的新快照替换旧值，不把 chunk 与最终消息重复相加；上下文压力只取输入侧，reasoning 不重复加到 output。[测试](../../../../../deepseek-harness/packages/llm/token-meter/tests/token-usage-projection.spec.ts#L127) 有对应样例，未在本轮执行。

**启发**：保留 raw receipt/normalizer revision，计费观察按 model_attempt_id+observation revision 去重；对话压缩不删除历史费用。

### 2.8 重试与等待可观察

[llm-retry](../../../../../deepseek-harness/packages/llm/llm-retry/src/index.ts#L114) 先 append 重试事件，再进入可取消 backoff，尊重提供方 Retry-After；plugin disposal 中止并排空活动等待。

**启发**：重试决策、延迟、次数、提供方原因必须可追溯，等待不占模型连接。LangChain 集成只保留一个 retry owner；平台还要加累计预算、deadline、远端未知和租户配额规则。

## 3. 不宜直接照搬的边界

| 源码事实 | 平台应采取的约束 |
|---|---|
| retry-policy 包含 always，直到成功/取消/销毁，可无次数上限 | 多用户付费平台禁止无界 always，增加硬尝试数、总deadline和预算；未知发送不得默认重试 |
| BlockAssembler.finish 在没有finish时默认stop | 仅在上游严格完整性合同成立时才有意义；平台不能把缺终态映射为业务成功。参考适配器有EOF检查，不能据此指控其正常路径必然误成功 |
| replay.parseArguments 非法JSON回落{} | 不用于实际工具执行参数；新平台保留 invalid_tool_calls，禁止非法参数变空对象继续执行 |
| token投影对未报告cache分桶用0，且只保留相邻step的last槽 | 可服务受会话顺序约束的展示投影；分布式账本按attempt/revision幂等，未知分桶留null，不能照搬单一last槽 |
| translate 将pendingUsage延迟到DONE才yield | 流被截断时可能已有原始usage但尚未发给消费者；平台可先记partial observation，终态才final，不把未知费用归零 |
| estimate 用固定4字符/token，TokenMeter.measure 每次复制surface节点 | 只作启发式上下文估算，不作收费真值/硬预算上界；不要每个token全量深拷贝历史 |
| freezeMessage structuredClone+deepFreeze；翻译器和assembler都维护内容 | 不变性有价值，但复制/重复组装可能有成本；不能不测量就宣称快。LangChain热路径尽量只有一个组装所有者 |
| 原生DeepSeek serializer always stream；该路线明确只支持文本 | 不把该路线能力等同于厂商所有API能力；LangChain无需强制所有generate都走stream |
| 参考包有会话/匿名用户归因和token计数 | 审阅范围未见完整多租户预算、货币价格、持久结算账本和跨副本限流；不称其已解决本项目的平台计费 |

## 4. 最主要的设计修正

借鉴的是稳定 seam、生命周期、快照、完整性和可复算机制，不是复制 Cordis/TypeScript 或重造 LangChain。优化重点应从“统一封装每家SDK和token协议”转为“用 LangChain 统一内部模型调用，把预算、身份、配置和费用事实补在正确边界”。完整候选见 [优化方案](05-langchain-optimization.md)，旧正式草案未变。
