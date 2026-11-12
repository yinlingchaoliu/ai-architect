# 分析

已固定当前源码、批准的 llmv2 设计、包依赖和 Git 起点，见 evidence/baseline.json。lib_request 的聊天、视觉、Embedding 和模型发现分别直连 SDK/requests，并在多个模块 import 时加载 dotenv。

用户本轮指定包名 lib_llm，优先于设计中的拟建 agent_platform.llm 命名空间。本轮实现进程内模型层和 lib_request 接入；不修改其他 Agent/服务的配置入口，也不修改其他 task 方案。Embedding/视觉需要独立显式能力配置，不能将 DeepSeek 文本端点伪装成 Embedding。

## 本轮边界与源码落点

起点 HEAD：`df9b41bd51fdf737a1495b57dc694f2bd050e3dd`，工作区初始干净。依赖版本以 [baseline](evidence/baseline.json) 和根 requirements 为准，使用已安装的 LangChain 1.5.0 / core 1.8.0 / openai integration 1.7.4；本轮未重新进行第三方依赖大版本升级。

| 原始问题 | 当前实现 | 验证 |
|---|---|---|
| 客户端分散加载 dotenv、拼认证、直连 HTTP/SDK | `lib_llm/config.py` 显式装配；`lib_request` 只接收或复用 Runtime | 配置优先级、导入无副作用、AST 边界检查 |
| 聊天与视觉返回形状不一致，requests 对象误作 SDK Choice | 聊天规范化 ChatCompletion JSON；视觉返回 SDK Choice | 旧入口与两类视觉客户端 wire 测试 |
| 伪 Embedding 调聊天接口 | 独立 embedding profile；DeepSeekEmbeddingClient 明确拒绝 | 向量维度/数值检查、独立 host/key 和拒绝测试 |
| 多层重试、同步调用每次建立资源的风险 | 内核持有 retry；SDK retries=0；共享连接池和同步桥 | 429、未知请求效果、TCP 连接复用、同步关闭 |
| Agent/Graph 接入可能绕过治理 | ManagedChatModel 原生 BaseChatModel，经同一内核 | LCEL、create_agent 工具、结构化、Graph messages 流 |
| 高并发缺少有界入口和取消释放 | 本地限并发、租户轮转、队列 item/bytes、超时、流背压 | 峰值并发、队列溢出、公平、早退/取消测试 |

## 实现与设计的对应

`runtime.py` 为单次调用内核；`provider.py` 为 LangChain/SDK 适配；`chat_model.py` 为原生协议桥；`stream.py` 和 `sync.py` 处理生命周期；`governor.py` 处理本地准入；`contracts.py` 提供版本化配置、上下文、usage 和治理 port。工具执行、Agent 循环、Graph checkpoint 和业务状态继续由上层负责。

配置发布落实为类型化 RuntimeSettings、原子 profile 注册、不可变 revision、旧视图固定和撤销取消。设计中的多表 YAML 发布器、外部 SecretResolver、控制面、Redis/持久预算后端未在本轮实现。production 模式要求可信调用上下文并注入 AccessPort、BudgetPort、QuotaBackend；这只是接入合同与拒绝缺项机制，不能代表生产治理已落地。

本轮不改批准的 llmv2 设计或其他 task 方案。执行期间检测到 `.gitignore`、`AGENTS.md`、根 README 和 WebUI README 等写集外变化，保留现状，归为并行工作区变化，未将其算作本轮实现。最终清单见 verification/write-set。
