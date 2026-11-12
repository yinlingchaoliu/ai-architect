# 08 · 验收方案、技术决定与评审

日期：2026-11-12。状态：**reviewed / self_review，设计验收计划**。本章测试矩阵为未来实施要求；本轮实际运行仅为源码/文档检查与零网络 payload probe，二者不能混为实现验证。

## 1. 需求追踪

| 用户需求 | 设计落点 | 实施接受条件 |
|---|---|---|
| 重新设计，不参考旧 llm 方案 | 本目录全部内容；源依据只含当前运行源码/DSH/官方资料 | 旧 llm 设计无内容读取、无覆盖，写集只在 llmv2 |
| 核心借鉴 deepseek-harness LLM | 注册、PreparedCall、流与 provider 边界、错误/重试分离 | 对照 [源码依据](01-source-reference.md) 的采用/不采用表评审 |
| 基于 LangChain 易用接入 | facade + ManagedChatModel + 原生消息/工具/结构化 | LCEL/create_agent/Graph/LangServe 兼容，绑定后仍受治理 |
| 合理分层与通用扩展 | LLM 单调用、Graph 流程、Harness Run 的职责表；adapter/ports | 增加第二 provider 不改业务 Agent 和 kernel 主流程 |
| 高性能、高并发 | 异步、连接复用、有界公平准入、背压和共享额度 | 在固定负载下报告资源/尾延迟/429/拒绝；容量约束不越界 |
| 完整方案与渐进实施 | 配置、合同、流程、异常、迁移、测试、回滚和重要文档 | 每个 LLM 内部阶段独立可运行，其他 task 调整先确认 |

## 2. 合同与行为测试矩阵（未运行）

| ID | 场景 | 必需结果 |
|---|---|---|
| T01 | 一个 profile 普通文本、空文本带工具调用 | 原生消息保真；后者不当空响应 |
| T02 | bind_tools/with_config/bind 后调用 | 仍经过相同 kernel，预算和额度实际生效 |
| T03 | create_agent 两轮工具调用、LCEL、StateGraph 子图 | 逻辑步/物理 attempt 关联，不重复执行工具/模型 |
| T04 | function_calling / provider schema / 非法输出 | 显式能力选择、Pydantic 校验；默认不隐藏修正循环 |
| T05 | text/reasoning/tool arguments 交错及多工具流 | id/index/原始字段保留；部分参数不提前执行 |
| T06 | finish chunk + trailing usage、重复 usage snapshot、缺失 usage | 最终值不重复累计，unknown 为 null，cache/reasoning 不重复加入总数 |
| T07 | EOF 缺 finish、length 截断、畸形 tool args | partial/incomplete/validation error；不宣告正常成功 |
| T08 | DeepSeek thinking 工具多轮历史回放 | 所需 assistant reasoning 在请求中完整保留；公共日志不显示正文 |
| T09 | SDK/client 与 wrapper 双层 callbacks | 一个 attempt 一次记账；公开 token 不重复 |
| T10 | 底层超时/429/5xx/连接失败 | 正确 code 和 request_effect；只有单一、有界 retry owner |
| T11 | 首个输出后失败、消费者 break、task cancel | 不透明重试；关闭迭代器/transport，释放许可并保持未知计费事实 |
| T12 | 同时约束 C/RPM/TPM、超大请求和队列满 | 拒绝/排队有界，无“拿 semaphore 后无限等 rate token” |
| T13 | 两个 alias/worker 用同一 account | 不叠加整份配额；shared 或静态分片策略实际生效 |
| T14 | 一个重载租户、一个小请求租户 | 公平调度、防饥饿，租户错误不熔断所有账号 |
| T15 | 配置发布中并发请求、冲突注册/CAS 失败 | 请求使用完整旧/新快照，没有混合 endpoint/key 或短暂空路由 |
| T16 | profile 更新、长寿 Graph、多步 Run | 在途绑定不漂移；新图按 owner 显式激活 |
| T17 | 密钥轮转、撤销、provider drain | 新调用新 secret version；撤销不能被旧 binding 绕过；共享 client 不提前关闭 |
| T18 | reserve/settle/sink 失败 | reserve 失败不付费；settle pending 不重发模型；sink 失败不伪造 provider error |
| T19 | 多租户同消息、不同 tools/profile/schema | 无共享可变历史/headers/回答缓存污染 |
| T20 | 同步桥、已有 event loop、stream 提前关闭 | 同 owner loop 阻塞调用拒绝；上下文与取消正确传递，无线程/连接泄漏 |
| T21 | shared backend 断开、lease 续租失败、worker 崩溃 | 不退为多份全额本地配额；orphan 预算和远端状态如实 unknown |
| T22 | 核心框架/provider SDK 升级 | 绑定、payload、replay、finish、usage 与关闭合同回归 |
| T23 | 自动 tracing / 显式 exporter / 异常 cause | 内部模型事件与外部内容投影分开；未批准正文不外发；公共错误不泄露鉴权信息 |

测试使用固定 fake 模型只证明图机制；MockTransport 证明 SDK 调用体，不证明真实网络；本地 HTTP/SSE 服务证明协议、连接和取消；真实 provider 验证精确模型模式；生产证据另列。必须保留这些证明层次。

## 3. 性能验证设计（未运行）

### 3.1 Fixture 与环境

固定 Python/包锁、CPU/内存、进程/worker 数、事件循环、HTTP 版本、客户端 limits、QuotaBackend 模式及网络位置。负载覆盖短/长输入、短/长输出、带工具 schema、慢首 chunk、长 reasoning、慢消费者；每类报告输入 bytes/token 估算及实际 output 分布。只比较相同 workload、相同 provider/quota、相同 tracing 策略的候选。

第一组本地可控测试采用 C=16、Q=32、有限队列 bytes：持续施压、所有请求都排队、慢消费者、取消风暴、fault injection 和配置切换。另以两 worker 测 shared/static_partition；这些是测试参数，不是生产默认规模。

### 3.2 可直接判定的资源不变量

- 实际活跃请求不超过配置本地上限；共享计数在其明确故障模型内遵守账户上限，崩溃后的远端 orphan 单独报告。
- 队列 item/bytes 不超过配置；超量调用快速拒绝；deadline 覆盖等待和退避。
- 相同 transport key 的客户端构造次数稳定；请求完成/取消后 active leases、任务和连接回到基线范围。
- 固定有界输入和输出下 RSS/heap 不随已完成请求数量线性增长；记录峰值与稳态，而非只看一次 GC。
- retries/physical attempts 与记录一致；SDK/外层不放大；部分输出之后没有自动拼接新生成。
- tenant 隔离和公平场景无永久饥饿；p95/p99 queue wait 和拒绝率按租户展示。

### 3.3 需要实测后定稿的目标

本项目缺少真实生产负载与 SLO。吞吐、p95/p99 total latency、TTFT、kernel CPU 开销、CPU/RSS 上限和允许拒绝率均为 **UNKNOWN / 待 L1-L4 基线确定**。实施候选可提出相对 raw provider/当前入口的开销阈值，但必须同时给硬件、输入分布、负载和原始结果，不能先写“支持万并发”或无来源 TPS。

真实 provider 压力验证必须有明确调用次数/费用/时间边界；既有密钥存在不等于本轮已进行或获准无限压测。本轮仅设计，没有发起付费请求。

## 4. 架构决定与替代方案

| 决定 | 采用理由 | 代价/重新评估条件 |
|---|---|---|
| A01 首期进程内库 | Python 调用和 native LangChain 最短路径，易于渐进接入 | 多语言/统一出口需求明显时再评估独立 Gateway |
| A02 原生消息 + ManagedChatModel | 保持 create_agent/LCEL 生态，避免完整消息体系双份维护 | 桥接方法和 model.profile 有框架版本风险，必须固定/回归 |
| A03 单一 kernel 请求治理 | 统一 quota/budget/deadline，不让 easy API 和 Graph 旁路 | 所有 provider/compat 入口必须注入；禁止直接泄露 raw client |
| A04 default 显式非思考；专用 replay 能力门槛 | 延续 S01 已验证模式，同时正面处理思考协议 | 新包/窄子类需单独验证；不假定集成页过时特性表适用 Flash |
| A05 不可变 revision + PreparedCall | 避免在途配置和 endpoint/credential 混配 | 长寿图需要 owner 切换新 binding，不能 magic hot reload |
| A06 共享账号 quota、按调用持有 lease | 高并发可控、不会 alias/worker 放大配额 | shared 后端是部署依赖；故障和 orphan 仍需保守治理 |
| A07 部分输出后不透明重试 | 防止回答拼接和不确定工具内容 | 部分失败需 UI/Harness 显式处理，用户可能看到 incomplete |
| A08 unknown usage/cost 保留 null | 事实与预算估计分离，重试/中断不伪造零值 | 旧模型返回类型要迁移，外层提供对账能力 |
| A09 不引入隐藏 Agent/业务队列 | LLM 单调用职责清楚，与 Graph/Harness 可组合 | 持久恢复和工具循环必须由外层提供 |

不采用“原生 SDK Manager 每 Agent 一份”“直接裸露所有 provider kwargs”“只用 asyncio.Semaphore 就称高并发”“完全重写 LangChain 消息/SSE”“Graph 外再套一层 Agent循环”等方案，理由和具体失败路径已在对应章节展开。

## 5. 本轮实际审阅与未解决项

设计自审覆盖：源码事实/借鉴差异、依赖方向、原生模型兼容、身份/配置、attempt/usage、流早退、多个 retry owner、多副本额度和原项目迁移。实际检查见 [run-01 复盘](run-01/03-review.md)及其机器可读回执。

尚需后续实施/决策：生产配额和负载/SLO；专用 DeepSeek adapter 全组合验证；外层 BudgetPort、配置服务和身份来源的实际实现；多副本 quota 部署；Graph owner 的 revision 切换接点；legacy consumer 对 nullable usage 的接受。这里给出合同和触发条件，不把未知项写成已上线能力。

本设计状态为 self_review，不是独立质量签认或用户已接受。需要实施时，先按本目录确定当前阶段具体写集和可运行验收；不会凭设计文档自动修改其他 task、安装新 provider 包或发起外部模型调用。
