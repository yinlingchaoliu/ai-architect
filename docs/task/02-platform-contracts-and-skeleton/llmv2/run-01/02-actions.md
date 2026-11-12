# 行动：本轮实际工作

| 顺序 | 实际行动 | 观察与证据 |
|---|---|---|
| 01 | 读取项目 AGENTS.md、arch 入口和本次相关子技能 | 按项目规范采用源码取证、分层/合同设计和自审；不批量加载无关技能 |
| 02 | 查询记忆目录的项目指针后回到当前 checkout | 历史仅用于定位；本轮事实按新 HEAD/dirty 与源码重新核对 |
| 03 | 找到相邻 deepseek-harness，固定 commit 和状态 | 47f9438，无 dirty；读取 llm 核心、DeepSeek adapter、retry、meter 和 agent-loop 消费边 |
| 04 | 回读当前运行源码和框架实现 | model 构造分散、原生 SDK/同步调用/局部 retry、usage 缺失为 0 等事实进入源码依据 |
| 05 | 核对官方 LangChain/DeepSeek/HTTPX 文档 | 区分 provider wire 能力与 adapter 能力、连接池/流关闭和模型结构化接口 |
| 06 | 下载读取 PyPI langchain-deepseek 1.1.1 wheel 的源码与 metadata | 校验 wheel hash；未安装或执行下载的 provider 包；候选元数据单独留证 |
| 07 | 运行现有 ChatOpenAI 本地 payload probe | 合成消息，无网络无真实密钥；reasoning_content 未进入 payload |
| 08 | 创建设计目录和初始元数据基线 | 仅 llmv2 写入；其他 491 个非私密文件初始 size/mtime 用于后续范围观察，不读取旧方案内容 |
| 09 | 编写完整专题、合同和图源 | 覆盖架构/API/provider/并发/配置/迁移/验收；所有拟建接口明确标注 |
| 10 | 执行定向文档、JSON/YAML/Python 示例和源码指纹检查 | 回执见 evidence/document-check.json；不运行旧 S02 llm 的检查器或代码 |
| 11 | 对同一候选自审与最终回读 | 文档/接口与未验证边界一致；没有真实 provider 请求、代码改造或压测 |

原有 .env/.env.local 未读取、未变更；没有保存 key、鉴权头、完整环境或模型内部隐含推理。全部网络请求用于读取官方公开资料/包源码，不使用用户模型凭据。

范围观察：设计期间检测到根 requirements 与若干安装说明等路径发生并行变更，已重新读取根依赖声明并修正本设计的现状段落；这些变更不属于本轮写集，未恢复/覆盖。最终元数据差异保存在 evidence/outside-observations.json。
