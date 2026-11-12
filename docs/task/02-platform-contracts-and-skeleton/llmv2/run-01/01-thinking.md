# 思考：设计依据与取舍

本记录是可观察依据、权衡与决定摘要，不记录模型内部隐含推理。

用户要求从源码重新设计通用 LLM 层，以 deepseek-harness LLM 为核心参考、用 LangChain 封装并支持 Agent Harness/Graph 分层、高性能及高并发。本轮只获准设计，写集限定 llmv2，不读取旧 llm 方案；已有其他 task 和工作区用户改动保留。

参考源码显式提供 registry、PreparedCall、block stream、provider adapter 和可取消的 retry 扩展。Python 项目已有 LangChain 消息/模型/Graph，不应再复制完整 Cordis/消息/SSE 栈。采用一个库中的 Facade/Bridge、kernel、adapter、transport，保留外层 Harness/Graph 的唯一控制权。

高并发瓶颈除了 I/O，还包括账号额度、长流占用、队列内存和重试放大。因此方案同时描述连接、C/RPM/TPM、tenant 公平、bytes 背压、deadline、部分输出及多副本 lease；未知容量不给伪造数值。

定向源码与本地 payload probe 发现 generic ChatOpenAI 不回传合成 reasoning 字段。专用 ChatDeepSeek 候选虽提取 reasoning，但未证明整个历史回放闭环。默认继续显式非思考；thinking+tools 以 adapter 合同及真实受控验证为能力门槛，不以集成包名推断可用。

保持 BaseChatModel 是易用性与生态组合的关键，但 bind_tools/with_structured_output/缓存可能旁路治理。模型视图必须不可变且继续进入 kernel，原生 provider 私有，SDK retry=0；native Graph profile 绑定与配置热更新需 owner 显式切换。

本轮使用项目 arch 及相关源码、分层、模块、协议、技术、图与审阅方法；不启动子 Agent，不修改全局技能或业务实现。
