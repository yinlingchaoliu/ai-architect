# 08 · 六类模型能力与统一易用 API

日期：2026-11-12。版本：v0.2。所有类名、调用和JSON均为拟合同样例，尚无可导入实现。机器可读请求样例见 [examples/unified-model-requests.json](examples/unified-model-requests.json)。

## 1. 同一调用方式，保留不同能力的输入输出

```python
models = model_service.for_context(trusted_context)
result = await models.ainvoke(request)
async for event in models.astream(stream_supported_request):
    consume(event)
```

request是具体请求类型，构造器自动固定ModelType；ModelResult封套一致，output强类型。六类不是六套客户端、认证或错误处理。调用方不解析requests.Response、choices或JSON字符串，不在业务里判断厂商。

| ModelType | 请求类与主要输入 | output | 流式声明 |
|---|---|---|---|
| LLM | LLMRequest：messages、tools、output_contract、LLMParameters | LLMOutput：message/blocks、text投影、tool_calls、structured_value、continuation_ref | 按模型stream/tool-stream能力 |
| TEXT_EMBEDDING | EmbeddingRequest：texts、purpose=query/document、EmbeddingParameters | EmbeddingOutput：vectors、indices、dimension、index_identity | 首版不支持，不模拟为聊天流 |
| RERANK | RerankRequest：query、带id的documents、RerankParameters | RerankOutput：items(original_id/index/rank/score)、score_semantics | 首版不支持 |
| SPEECH2TEXT | SpeechToTextRequest：audio_ref、SpeechToTextParameters | TranscriptOutput：text、segments、language、duration、可选confidence | 仅实现已声明的转写增量能力 |
| MODERATION | ModerationRequest：带id的items/blocks、ModerationParameters | ModerationOutput：每项flagged/categories/scores、模型标签规范版本 | 首版不支持 |
| TTS | TTSRequest：text、TTSParameters(voice/language/format/speed) | AudioOutput：audio_ref、MIME/codec、duration、sample_rate | 按音频chunk能力声明 |

首版只定义六类合同，不代表供应商都已配置。发布目录中缺该类型或未验证时返回MODEL_NOT_CONFIGURED/CAPABILITY_UNSUPPORTED，不能为了让例子成功而自动调用聊天模型冒充。

## 2. LLM：文本、图像理解、工具和结构化输出

```python
text = await models.ainvoke(LLMRequest(
    model_ref="chat.general@r1",
    messages=[Message.user("写一段说明")],
    parameters=LLMParameters(max_output_tokens=512),
))
print(text.output.text)

vision = await models.ainvoke(LLMRequest(
    model_ref="chat.vision@r1",
    messages=[Message.user([
        TextBlock("描述图片"),
        ImageBlock(artifact_ref="artifact://example/photo"),
    ])],
))
print(vision.output.text)
```

视觉理解是LLMRequest + image block + vision feature，不再提供不同返回结构的vision_image_path/vision_image_url协议。旧path/URL先经媒体入口校验、取回和授权生成artifact_ref；普通模型调用不任意读取主机文件或抓取URL。

工具Schema和tool_call_id保留，argument delta未完成不得执行。ModelService不执行工具；LangChain/Harness处理工具循环与ToolStrategy。Native JSON Schema与工具策略是不同能力，不能静默互换或忽略非法输出。文本便捷属性只拼接可见text，不将reasoning当最终答案、不丢原始块。ToolStrategy的纠错若显式启用，属于受Run总预算/步数约束的新逻辑call，各次独立记账；Graph恢复同一次模型步骤复用operation_key，下一轮/纠错步骤使用新的稳定操作ID，不能用Run ID充当所有调用的幂等键。

## 3. TEXT_EMBEDDING：批量向量与索引身份

```python
batch = await models.ainvoke(EmbeddingRequest(
    model_ref="embedding.knowledge@r1",
    texts=["文档A", "文档B"],
    purpose="document",
))
query = await models.ainvoke(EmbeddingRequest(
    model_ref="embedding.knowledge@r1",
    texts=["用户问题"],
    purpose="query",
))
```

一次输入列表按原顺序返回vectors和indices；每个向量维度一致且有限数值，不用向量空值替代错误。query/document可有不同前缀或训练语义，由adapter/entity声明；query模式首版只接收单条，document支持有界批量。

index_identity至少包含Provider/模型revision、dimension、预处理/任务前缀、归一化与距离语义。维度相同不等于可混用；更换Embedding模型需要索引重建/迁移决定，不能仅修改chat默认值。长文本切分属于检索预处理或显式批计划，不允许框架隐藏分块后无记录平均成一个向量。

一次逻辑批处理可能拆为多个物理请求，服务记录BatchPlan，每批独立尝试和usage，最终合并保持顺序。部分批失败默认整调用失败并保留已发生usage；如未来开放partial结果，必须显式声明missing indices，不回成功空向量。

## 4. RERANK：模型重排与检索分工

```python
ranked = await models.ainvoke(RerankRequest(
    model_ref="rerank.knowledge@r1",
    query="通用模型层",
    documents=[DocumentInput(id="d1", text="模型服务接口"),
               DocumentInput(id="d2", text="界面主题")],
    parameters=RerankParameters(top_n=1),
))
print(ranked.output.items)
```

输出保留输入id/original_index、rank与score；score可能是未校准相关度，必须声明其语义/范围，不把任意分数当概率。top_n范围、批大小、截断策略和稳定tie-break明确校验。Provider未返回score时不得制造为0或1。

lib_request的cosine_similarity是本地向量相似度，属于retrieval helper，不是RERANK模型。需要专用rerank时才按本类型路由；LLM打分是另一个明确声明/计费的流程，不能作为无感成功降级。

## 5. SPEECH2TEXT 与 TTS

```python
transcript = await models.ainvoke(SpeechToTextRequest(
    model_ref="speech.input@r1",
    audio_ref="artifact://example/input-audio",
    parameters=SpeechToTextParameters(language="zh"),
))
print(transcript.output.text)

audio = await models.ainvoke(TTSRequest(
    model_ref="speech.output@r1",
    text="欢迎使用统一模型服务。",
    parameters=TTSParameters(voice="configured-default", format="mp3"),
))
print(audio.output.audio_ref)
```

STT输入使用受控audio_ref与真实MIME/编码/大小，时长由可信媒体提取或provider回执确认，不相信用户自报计费秒数。segment有稳定ID、起止时间和revision；实时修订是replace，不是把旧文本不断append。confidence缺失为null；language/duration也按来源标记。

TTS输出走二进制/对象存储引用，不塞进text或返回完整SDK对象。流式音频含chunk顺序、codec、MIME和必要头信息；不能把多段独立WAV文件直接拼成一段流。voice/格式/采样率/速度按模型参数Schema校验，未知voice明确拒绝。文本/音频上限与取消、媒体文件写入最终化均有独立验证。

## 6. MODERATION：审核预测与业务政策分开

```python
moderation = await models.ainvoke(ModerationRequest(
    model_ref="moderation.content@r1",
    items=[ModerationItem(id="input-1", blocks=[TextBlock("待审核内容")])],
))
```

输出对应每个input id，保留flagged、categories/scores和模型标签规范版本。厂商未提供某字段时留null，不能把空响应/异常解释为安全。业务是否阻断、人工复审或使用哪条阈值政策由上层决定；模型调用失败必须显式返回错误，让上层采取配置的fail-closed/人工规则，不假造flagged=false。

多模态moderation仅在entity声明支持相应blocks时可用；不能用文字提示审核代替专用能力而保持相同结果语义。

## 7. 默认值、参数、结果和同步兼容

按ModelType分别配置默认ModelBinding。LLMRequest可以省model_ref使用chat默认；EmbeddingRequest必须解析到embedding默认，不能继承chat.general。显式model_ref与请求类型不匹配时发送前拒绝；参数默认不覆盖显式0/false值，不根据未知厂商悄悄clamp。

ModelResult包含output、usage及独立settlement_status。LLM是tokens，TTS可能是字符/音频单位，STT可能是秒；调用封套不变但计费维度不同，详见 [03](03-usage-and-billing.md)。所有失败使用同一ModelError taxonomy，业务不解析provider原始错误JSON。

高并发入口统一使用async方法。旧同步lib_request类仅作为过渡Facade，委托明确生命周期的SyncModelClient：专用受控后台loop/连接池执行同一ModelService逻辑，并用有界队列/timeout同步等待。不能在正在运行的event loop中阻塞或asyncio.run，也不能跨loop共享AsyncClient。新业务不再新增同步厂商类；兼容SDK Choice等历史返回形状的具体限制见 [06](06-project-integration.md)。

## 8. LangChain 组件接入

Agent获取bootstrap提供的PlatformChatModel，向量库获取PlatformEmbeddings；它们是薄framework bridge，不是新的厂商实现。框架内部支持原生投影，公共业务仍使用上述ModelClient。两种消费者共享prepare、budget、retry与usage owner，不能通过直接原生模型调用绕过治理。

当前LangChain Embeddings和Compressor基类的async默认实现可能落线程池；不是所有能力都有同一个LangChain基类。所选适配器必须验证原生async、真实stream/取消和完整usage来源，不因为加了Runnable包装就宣称具备高并发能力。
