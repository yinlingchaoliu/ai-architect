# 复盘

结论：用户本轮授权的 `lib_llm` 实现与 `lib_request` 接入切片完成。审阅者为当前执行 Agent，自审；未安排独立 Agent 审阅，未取得本轮用户验收，未做生产部署。

## 需求验收

| 用户要求 | 结果与证据 |
|---|---|
| 按确认的 llmv2 设计实现 lib_llm | 已实现原生 facade、单次调用内核、LangChain provider、同步桥、有界流和治理 ports；见包 README 与分析中的设计映射 |
| lib_request 接入 | 聊天、视觉、embedding、发现和 similarity 客户端走 lib_llm；真实文本路径通过 |
| 环境配置只从 lib_llm 接入，本轮只处理 lib_request | lib_request 源码无 os/dotenv/provider 客户端直接导入；配置优先级、跨 host key 隔离和 import 无副作用通过 |
| 分析、思考、复盘、反思写到 run-02 | 当前目录文档及 evidence 完成，其他 task 方案与批准设计未改 |

## 验证与证据层级

1. **本地回归：56 passed，0 failed，0 skipped。** [tests.xml](evidence/tests.xml) / [tests.log](evidence/tests.log)。包括真实 LangChain/Graph 对象与 HTTPX mock wire、生命周期、并发、共享 port 注入和原客户端兼容。3 项上游依赖弃用警告来自兼容 UI/RAG 路径，未将警告当失败或悄悄移除。
2. **本地真实协议：通过。** ThreadingHTTPServer 实测 TCP/HTTP/SSE，3 次连续请求复用同一客户端 socket；尾部 usage、完整结束和关闭通过。它证明本机协议与连接复用，不代表公网模型吞吐。
3. **真实 DeepSeek：3/3 通过。** 最终回执 [live-model.json](evidence/live-model.json) 绑定源码 SHA256；`lib_request → lib_llm` 文本、流式、ManagedChatModel 结构化成功；一个连接池、Runtime 关闭。模型为 deepseek-flash，非思考，64 token cap、单次尝试。无全会话费用审计或模型质量评测。
4. **安装与回读：通过。** 两个本地 editable 包可导入，pip check 无冲突；实际安装信息与核心源码、批准设计未漂移的检查写入 [verification.json](evidence/verification.json)。仅复用现有根环境并安装本地包，未声称从空环境重新安装整个项目。

## 兼容变化

- 聊天仍返回 JSON 字符串，视觉仍支持读取 `.message.content`，embedding 返回 float 列表；响应为规范化结果，不保留所有厂商私有字段。usage 未知保持 null。
- DeepSeekEmbeddingClient 原有伪向量路径改为显式不支持。使用前需配置真实 embedding provider。
- 原公开底层 key/base_url/SDK client 不再暴露；业务通过 profile/runtime 注入。enableDebug 保留方法，不再输出敏感正文。
- 原生 strict JSON schema、thinking replay、透明 fallback 未验证即拒绝。不要依赖这些未实现行为。

## 未证明/未实现

真实视觉、真实 embedding、真实模型 tool loop、多副本 Redis、持久预算结算、外部 secret store、控制面 YAML 发布器、故障恢复持久化、生产压测均未执行或未实现。工具循环和上述治理 port 使用本地受控 fixture；两 Runtime 注入共享内存后端测试不等价于跨进程或跨机器验证。

本地默认治理适用于单 Runtime/单进程；默认16活跃、64排队等是可配置上限，不是测得性能。TPM 为保守权重，无精确上下文长度估算或费用模型。其他应用尚未迁移，原有 dotenv 入口继续存在。完整平台设计不能因为本轮切片完成就整体标完成。

写集外并行改动保留，未参与本轮实现归因。回滚采用限定路径和隔离目录验证，详见 [接入与回滚](05-integration-and-rollback.md)。
