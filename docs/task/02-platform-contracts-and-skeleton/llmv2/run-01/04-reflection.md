# 反思：限制与下一步输入

本轮最有价值的做法是从 deepseek-harness 真正的 LLM/agent-loop 边界取证，再看 LangChain 已提供的能力，而不是从旧方案继续加层。这样可保留 prepared/registry/stream 的原则，同时减少重复消息和执行框架。

参考实现也不是不可变真理。usage 计数口径、EOF 默认、thinking 历史传回及 always retry 等行为需要对照目标 SDK 和当前 provider 规则分别处理。不能照抄行为后用“参考过优秀项目”替代正确性。

native LangChain 易用性与平台治理必须同时成立：任一 binding、结构化 wrapper、全局 cache、SDK retry 都可能成为旁路；实施验证应把这些路径作为高优先级，而不只验证 facade 返回一句文本。

高并发架构必须展示负载边界与失败代价。加 worker/连接池本身不会扩大账户配额；lease 过期也不证明远端请求终止。需要先做本地可控压力与取消/故障测试，再按真实生产负载设 SLO。

下一消费者是用户/实现负责人：确认本目录总体边界，选择 L0-L1 的具体代码写集；补齐实际账号额度、预算端口、身份与部署条件；再按阶段跑协议、Graph、provider 和容量验证。本轮没有替这些未知项填零，也没有用旧 S02 llm 方案倒推本设计。
