# 思考：依据与决定

只记录可观察判断摘要。采用现有锁定 LangChain 集成，实现一次调用的统一内核与原生 BaseChatModel 桥接，不新增 Agent 循环。配置在 lib_llm 入口显式加载，优先级为进程环境 > .env.local > .env，避免 import 副作用和模块间重复 getenv。

保留 lib_request 对外方法与主要返回形状，SDK/HTTP 调用全部移入 lib_llm。先验证离线 wire、原生图接入、并发/取消/流与配置隔离，再用已获准 DeepSeek 配置做有界真实文本检查。生产共享额度、思考工具回放等未通过能力显式拒绝，不能用空实现标完成。

## 已采用的取舍

1. **只保留一个环境装配点。** `dotenv_values(interpolate=False)` 合并 `.env`、`.env.local` 和进程环境，不调用 load_dotenv、不修改 os.environ。显式空值也是覆盖，不能悄悄从低优先级找回旧 key。构造 Runtime 后使用固定配置；请求不重新读文件。
2. **原生协议放在治理内核外侧。** ManagedChatModel 向 LangChain 提供 AIMessage、tool_calls 和 chunks；实际网络操作仍通过内核。只由外层发公开 token，内层 provider 禁止隐式 Graph streaming 传播，防止 token 重复。
3. **一个 Runtime 绑定一个事件循环。** 异步应用显式 lifespan；同步兼容入口复用一个 portal 线程和 loop。HTTP 连接不能在多个 loop 间迁移，owner loop 内调用同步方法直接报错。
4. **容量明确有界。** 限制活跃数、队列项/bytes、批量大小、输入/输出、流队列、profile/provider 历史版本。租户轮转控制排队机会；未做生产吞吐承诺。TPM 是 bytes + 输出上限的保守权重，不是精确 tokenizer 或计费。
5. **请求效果与结算分开。** 已产生输出后不能透明重试；缺 usage 保持 unknown；未发送请求释放预算预留，已发送但无法确认则标 unknown，结算失败标 pending，不能再次生成来“补偿”。
6. **能力按已验证范围声明。** DeepSeek 固定非思考；未验证的 reasoning replay 输入拒绝。结构化走 function calling + Pydantic，返回 `(parsed, LLMResponse)`，不内置修复循环。视觉/embedding 使用独立能力配置，跨 host 必须显式凭据。
7. **动态注册先做进程内合同。** CAS 防止覆盖并发发布；profile 和 provider revision 不可重写；已绑定视图保留旧快照；撤销取消匹配调用。历史达到容量后拒绝发布，需 drain/重建 Runtime，不无限保留旧连接。

以上是实现决策摘要与取舍，不记录模型内部推理过程。剩余的分布式后端和控制面问题只作为后续输入，不越权修改其他 task。
