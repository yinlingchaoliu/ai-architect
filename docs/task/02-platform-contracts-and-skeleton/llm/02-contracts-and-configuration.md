# 02 · Provider、模型实体、配置与公共调用合同

日期：2026-11-12。版本：v0.2。状态：设计合同，正式类型/Schema与实现尚未创建。常见调用和六类输出见 [08](08-model-types-and-api.md)。

## 1. Provider 与 ModelType

ModelType v1固定六个能力族：

```text
LLM = llm
TEXT_EMBEDDING = text-embedding
RERANK = rerank
SPEECH2TEXT = speech2text
MODERATION = moderation
TTS = tts
```

这是本项目按用户要求选择的首版集合，不声称Dify当前所有SDK仅有这六项。新增类型必须同时提供请求/结果/参数/计量/错误/适配器合同，不能仅加枚举后就声称支持。Vision、tool_calling、structured_output等是具体模型的特性，不与ModelType混用。

| 对象 | 必需内容 | 身份/生命周期 |
|---|---|---|
| ProviderDefinition | provider_id、display_name、supported_model_types、credential_schema、配置模式、允许的adapter kinds | 已安装插件/受审配置定义；不含用户secret |
| ProviderInstance | instance_id、tenant_id、provider_id、endpoint_ref、credential_ref/version、配置revision、enabled状态 | 某租户配置的供应商实例；可用同厂商多个账户/部署 |
| AIModelEntity | model_id、provider_instance_ref、model_type、revision、features、parameter_rules、input/output_schema_ref、properties、price_ref | 具体模型能力规范，发布后不可变 |
| ModelBinding | model_ref、model_type、tenant scope、目标entity revision、策略revision | 业务别名/按类型默认值；显示名不是主键 |
| CapabilityAdapter | adapter_kind、支持的ModelType及协议版本、能力/错误/usage/replay映射 | 平台预安装实现；由ProviderInstance和entity装配 |

Provider回答“有什么”，请求类的ModelType回答“要什么能力”，ModelBinding解析到具体模型。credential验证通过不等于模型/特性都可调用；目录发现只提供候选ID，不能发明其Embedding、vision或流式能力。

## 2. AIModelEntity 与能力校验

Entity主键至少包含Provider实例、model_type、model_id和revision。其规范包括：

- features：vision、tool_calling、parallel_tool_calling、stream_tool_calling、structured_output及其Schema子集、reasoning、stream等；每项有documented/contract_tested/live_verified/disabled证据状态。
- parameter_rules：类型、默认、是否必需、枚举、范围、互斥组合与明确的厂商映射。例如思考模式下不生效的temperature不得默默接受；不支持stop应拒绝。
- properties按ModelType区分：LLM上下文/输出上限；Embedding维度、query/document模式及索引身份；Rerank批大小与score语义；STT文件大小/格式/语言；TTS声音/编码/采样率；Moderation输入模态和标签集合。
- input/output_schema_ref明确能力输入与结果结构；price_ref指向独立不可变价格，不能把前端展示单价当当前账户实际价格。

先检查type，再检查features，再检查parameters/输入限制。空能力字段表示unknown，不等于全部支持；model_type不匹配返回MODEL_TYPE_MISMATCH。多模态LLM不自动获得TTS或STT能力，除非对应类型也发布了独立实体/合同。

## 3. 对上层的统一API

以下为拟接口语义：

```python
class ModelClient(Protocol):
    async def ainvoke(self, request: ModelRequest) -> ModelResult: ...
    def astream(self, request: ModelRequest) -> AsyncIterator[ModelEvent]: ...
    async def list_models(self, model_type: ModelType | None = None) -> list[AIModelEntity]: ...
    async def describe(self, model_ref: str, model_type: ModelType) -> AIModelEntity: ...
    async def inspect(self, call_id: str) -> CallObservation: ...
    async def cancel(self, call_id: str) -> CancelObservation: ...

class ModelService(Protocol):
    def for_context(self, trusted_context: CallContext) -> ModelClient: ...
    async def prepare_call(self, request: ModelRequest, context: CallContext) -> PreparedCall: ...
```

ModelRequest是六类请求的discriminated union；每类自带固定model_type与类型化parameters，构造器默认contract_version=models.v1。ModelResult以同一封套返回，但output是对应LLMOutput/EmbeddingOutput等，实施时用overload/generic保证静态类型，不以Any字典替代合同。普通调用者只需ainvoke/astream，不需要手工准备。

for_context不会修改ModelService.current_user，只创建每请求只读视图。CallContext来自API认证/Runtime，包含tenant、subject、charge account、可选Run/Task/Runtime Attempt、budget grant、deadline、trace等。普通body、metadata、模型输出或RunnableConfig都不能覆盖可信身份。每次调用生成独立call_id，传输request_id和厂商model_attempt_id另存。

### 公共封套

| 对象 | 结构 |
|---|---|
| 公共请求字段 | contract_version、由请求类固定的model_type、可选model_ref、parameters、受限metadata、可选operation_key |
| 公共结果字段 | call_id、model_type、resolved_model_ref、output、finish_reason、UsageObservation、settlement_status、受权限控制的receipt_ref |
| 业务文本便捷属性 | LLMOutput.text/TranscriptOutput.text只投影文本，不丢失原blocks/segments；EmbeddingOutput.vectors是向量列表，不要求解析SDK响应 |
| 标准错误 | code/category/retryable/remote_outcome/call_id/safe_message/retry_after_ms/details_ref |

operation_key由受控客户端生成或Runtime稳定操作ID提供，同一次传输/Graph恢复重放保持不变；同tenant同key异请求指纹冲突。指纹不含trace或当前时间等易变项。幂等命中先读原调用，不能因active别名已变化就重发。

## 4. Provider / Adapter 插件合同

```text
ProviderPlugin.describe() -> ProviderDefinition
ProviderPlugin.validate_credentials(instance_snapshot, secret_resolver) -> CredentialObservation
ProviderPlugin.discover_models(instance_snapshot) -> DiscoveredModel[]
ProviderPlugin.resolve_model(instance_snapshot, model_id, model_type) -> AIModelEntity
ProviderPlugin.create_adapter(binding_snapshot, transport_lease) -> CapabilityAdapter

CapabilityAdapter.ainvoke(prepared) -> CapabilityResult + observations
CapabilityAdapter.astream(prepared) -> AsyncIterator[InternalFrame]
CapabilityAdapter.capabilities() -> AdapterCapabilities
CapabilityAdapter.aclose() -> None
```

不支持流式时，astream在第一个可见事件/HTTP建流之前明确拒绝；不是返回一个最终值就假称真流式。LLM流事件是一等合同，非流式可复用同一规范化/最终化，也可以走LangChain原生ainvoke；不强制Embedding/Rerank等都实现流式。

注册使用先校验后原子替换的handle，可dispose/replace；重复注册冲突保留旧版本。模块内只有一个Provider/AdapterRegistry，不另维护一套LangChain供应商注册权威。请求捕获注册对象和配置快照，旧handle在引用排空后关闭。实现只允许allowlist中的预安装插件，不执行用户上传代码。

## 5. PreparedCall：一次准备与一次消费

绑定字段：请求规范化快照与指纹、ModelType/ModelBinding/AIModelEntity、ProviderInstance/endpoint/protocol、adapter registration、配置/能力/价格/策略revision、credential version、可信context、总deadline、分批计划/尝试预算。secret原文不进入可序列化快照，取消通道与静态配置分开。

状态候选为prepared → dispatching → finished/failed/canceled/unknown；prepared也可因撤销/过期进入rejected/expired。PreparedCall只能被ainvoke或astream消费一次；消费表示启动唯一Runner，可包含策略允许且已登记的有限ModelAttempt，不表示每次重试再消费PreparedCall。重复消费或篡改已固定快照报INVALID_PREPARED_CALL。active别名发布新revision不算在途快照被篡改。未消费不提前长期占用模型连接；发送前重新校验当前撤销、租约和预算授权。

准备动作与实际厂商请求之间不能依赖全局latest再次解析。对LangChain Graph，框架绑定tools/response_format可能产生额外Schema，准备快照必须纳入这些配置和预估开销；语义快照不自动等同完整HTTP payload。实施时用实际发送fixture校验，不能调用私有框架函数假装已冻结线协议。

内存一次flag不是跨进程幂等。持久调用/尝试/dispatch intent和结果观察属于共享治理接口，后续S04实现。一次批Embedding等若分多次厂商请求，每个真实请求有独立ModelAttempt；总PreparedCall约束所有批次，不允许SDK隐藏重试绕过上限。有限重试沿用同一模型/协议快照；跨模型fallback首版不隐式执行，若后续授权启用，须创建关联的新call/PreparedCall并重新校验能力、价格和额度，不在旧快照里偷偷换模型。

## 6. LLM 消息、标准流与回放

消息包含稳定message_id、role、blocks、source、tool_call关联及受控continuation。role可为system/user/assistant/tool；工具结果不得被当作system权限。blocks支持text、reasoning、image/document/audio引用和工具调用，新增块必须连同adapter、持久、显示/压缩规则一起验证。

ModelEvent公共头为event_version、call_id、model_type、model_attempt_id、sequence、emitted_at。继承DeepSeek的核心词汇：

| 事件 | 语义 |
|---|---|
| start / attempt-start | 受理与实际尝试分开，start不表示已产生厂商费用 |
| block-start | index/block_id和block_type，允许多个工具块交错 |
| text-delta / reasoning-delta | 明确append增量；reasoning默认受可见性控制，不自动当作用户答案 |
| tool-call-delta | call_id/name/arguments fragment；未收齐不得执行 |
| block-end | 完整块/完整性结果；是authoritative快照，不向UI再次append其完整文本 |
| transcript-delta | STT增量或修订，含segment_id/revision，不能把修订直接拼接 |
| audio-delta | TTS二进制chunk索引/编码/MIME信息；wire传输按规定投影 |
| usage | status/source/observation revision及计量单位，final之前可有partial |
| finish | 唯一终态：stop/tool-calls/max-tokens/refusal/error/aborted/unknown，带结果引用和独立结算状态 |

终态后不继续发内容；连接丢失可能收不到finish，应通过inspect观察。缺终态不默认stop。用户观察Agent事件连接断开不等于取消Agent；实际模型consumer退出应关闭本次生成并记录停止观察。

Provider原生签名/response ID/reasoning passback元数据由adapter持有versioned replay envelope，绑定tenant、provider instance、协议、模型和revision。对外仅给安全引用；跨厂商不直接回传。同一个Adapter类或实例不等于获得跨租户访问权。

LangChain内部保留原生块信息，但其AIMessageChunk usage通常是additive，公共usage observation可能为cumulative/final。适配器必须区分：重复累计快照不能放进可相加的usage_metadata；平台按attempt+observation revision归并，不能把callback、最后AIMessage和stream快照各记一笔。

## 7. 配置发布与凭据

配置分三层：供应商规范 → 租户ProviderInstance → 分类型的模型实体/别名。例子为设计数据，不是已发布配置：

```yaml
schema: models.v1
provider_instance:
  id: deepseek-primary
  provider_id: deepseek
  tenant_scope: authenticated-tenant
  endpoint_ref: endpoints/deepseek-official
  credential_ref: secret/deepseek/platform-key@v1
  revision: provider-r1
model:
  id: flash
  model_type: llm
  provider_model: deepseek-flash
  revision: model-r1
  features: [text_input, text_output, tool_calling, stream]
  parameters:
    reasoning: disabled
  adapter_kind: langchain-chat-compatible
  price_ref: prices/deepseek-flash@to-be-verified
binding:
  alias: chat.general
  model_type: llm
  revision: r1
```

待核验价格占位不能通过生产付费发布；示例不表示当前模型已对所有特性完成测试。Embedding等五类必须分别配置，不由OPENAI_MODEL或全局base URL推导。provider credential可验证而某模型无权限，仍需模型级验证。允许本地无凭据模型时也须管理员发布的endpoint和出站规则。

配置模式可为predefined、自定义模型和remote discovery。发现的ID先进入候选，通过类型/特性/参数/凭据/出站验证后再发布。draft → validate → 受控canary → CAS发布active revision；回滚改变新请求指针，在途保留旧快照，紧急撤销发送前检查。credential轮换创建新版本与新池，旧池排空/撤销关闭。

## 8. 错误与可选远程接口

稳定错误至少覆盖INVALID_REQUEST、MODEL_NOT_CONFIGURED、MODEL_TYPE_MISMATCH、MODEL_REVOKED、CAPABILITY_UNSUPPORTED、PARAMETER_UNSUPPORTED、UNSUPPORTED_STREAM、CONTEXT_TOO_LARGE、AUTH_REQUIRED/ACCESS_DENIED、IDEMPOTENCY_CONFLICT、BUDGET_EXCEEDED、PRICE_UNAVAILABLE、OVERLOADED/RATE_LIMITED、PROVIDER_PROTOCOL_ERROR、OUTPUT_INVALID、DEADLINE_EXCEEDED、CANCELED、OUTCOME_UNKNOWN、LEDGER_UNAVAILABLE。

错误含明确retryable与remote_outcome，但由唯一Runner结合剩余预算/deadline决定，不靠看到某个HTTP码就无界重试。Moderation调用失败不返回“审核通过”，空Embedding不返回成功向量，非法tool JSON不变成{}继续执行。详细能力错误见 [08](08-model-types-and-api.md)。

远程ModelClient可使用POST /v1/model-calls:invoke、POST /v1/model-calls:stream、GET /v1/model-calls/{id}、POST .../{id}:cancel、GET /v1/models?model_type=...；入站认证绑定同一context，type discriminator决定请求Schema。Admin Provider注册/validate/publish/revoke接口独立授权，不允许普通用户任意提交base URL、鉴权headers或secret_ref。鉴权/幂等/能力校验在SSE headers前完成，建流后的错误用finish表达。
