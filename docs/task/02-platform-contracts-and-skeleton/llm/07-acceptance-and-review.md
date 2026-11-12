# 07 · 需求覆盖、验收合同与本轮审阅

日期：2026-11-12。版本：v0.2。用户已确认DeepSeek主方案并授权本次重写；实现阶段尚未开始。review_mode=self_review，没有独立评审签认。实际文档检查见 [design-validation.json](design-validation.json)，不以文档检查代替服务验收。

## 1. 本轮要求映射

| 本轮要求 | 正式设计落点 | 设计决定 |
|---|---|---|
| DeepSeek Harness llm为主方案 | README、01、02、05 | ModelService稳定服务契约，注册、prepare_call、快照、标准流、回放和计量分离 |
| LangChain统一封装 | 01、04、08 | 能力适配器复用原生框架，业务用ModelClient，Graph/向量库用薄Bridge，共用一个执行内核 |
| Provider回答有什么 | 02 | ProviderDefinition/租户ProviderInstance、认证、发现候选、校验发布与模型目录 |
| ModelType回答要什么 | 02、08 | 六类请求自动固定类型；按类型默认值、权限/特性/参数校验，保留真实输入输出 |
| AIModelEntity声明能力与参数 | 02、08 | 每模型能力实体有features、parameter_rules、properties、输入输出Schema与证据状态 |
| 上层调用统一且易用 | README、02、08、JSON样例 | 同一for_context/ainvoke/astream与ModelResult/ModelError，结果强类型而非任意字典 |
| 多用户并发与性能 | 04 | 共享只读资源、原生异步、请求隔离、池复用、单次流投影、有界背压与共享准入 |
| 消息用量与费用 | 03 | 多计量单位、原始回执/归一化/成本/收费分离，缺证保留null/pending |
| 整理当前lib_request混乱调用 | 06 | 已核对实际源码，逐旧接口迁移到统一合同；兼容Facade不能另建发送路径 |
| 后续扩展保持上层无感 | 05末节 | 仅保留后续接入方向，不在本模块设计中划分外部产品职责 |
| 独立设计，保护其他task | 本专题及run-01/rewrite-01 | 不调用未完成的arch技能；不更改其他task的方案内容或状态 |

## 2. 拟实施验收矩阵

下表全部是**未来实现的验收要求，本轮not_run**。fake合同验证、真实厂商、持久治理分别出回执，不能把一项通过扩成全能力/全仓通过。

| ID | 场景 | 必须证明的行为 | 阶段 |
|---|---|---|---|
| U01 | 六类请求与结果 | ModelType固定、类型化参数/输出、稳定错误；JSON与Python请求语义一致，不泄漏SDK Response/Choice | S02合同 |
| U02 | 无key导入与按需装配 | import纯合同/客户端不初始化SDK、不读取secret、不发网络；未安装extra有明确错误 | S02/S03 |
| U03 | 分类型默认值/显式模型 | Embedding不继承chat默认；类型不匹配、未知特性/参数发送前拒绝；显式0/false保留 | S02 |
| U04 | Provider发布/认证 | 凭据通过不冒充所有模型通过；发现结果需发布；租户只能访问授权实例；配置验证失败不替换旧handle | S02/S03 |
| U05 | PreparedCall与轮换竞态 | endpoint/key/adapter同一快照，await前后不混代；单次消费可含有限已登记尝试；active别名变化不篡改在途请求 | S02/S03 |
| U06 | 文本/视觉迁移 | 同LLMRequest/LLMOutput；model_ref真正生效；无硬编码视觉模型；媒体授权独立；错误HTTP旧路径退出 | S03 |
| U07 | 工具/结构化/回放 | bind_tools/profile/response_format保真；非法工具参数不变{}；Schema失败仍保留模型usage；续答不跨tenant/provider | S03 |
| U08 | 标准流与框架流 | 原生与公共投影语义一致；block-end不重复append；usage快照不误加；唯一finish；缺终态显式未知 | S02/S03 |
| U09 | Embedding批量 | query/document正确、顺序/维度/有限数值、索引身份、实际batch数和逐请求usage；长文本不隐藏平均 | S02/S03 |
| U10 | Rerank | id/index/score语义/稳定并列排序，缺score不造0；cosine检索不假称专用模型 | S02/S03 |
| U11 | STT/TTS | segment修订不拼接重复文本；编码/MIME/voice与媒体长度正确；音频chunk可解码；取消清理工件 | S02/S03 |
| U12 | Moderation | 输出映射原input id，标签版本/缺失字段显式；异常或空结果不返回审核通过 | S02/S03 |
| U13 | 多Provider替换 | 相同类型fixture替换至少两种实际协议实现，上层合同不变；超出能力明确拒绝 | S02 fake / S03具名真实 |
| U14 | 原生异步与同步边界 | 各integration验证native async/取消；同步Facade独立loop资源，无跨loop客户端/数据库池，无event loop阻塞 | S03 |
| U15 | 多用户隔离 | 并发history/tools/headers/collector/timing/continuation不串；body伪造tenant无效，查询/取消按身份授权 | S03/S04 |
| U16 | Bridge唯一路径 | Graph/向量库不绕过ModelService；默认ProviderStrategy/ToolStrategy/profile有具名互通用例；无重复token/回调入账 | S03 |
| U17 | 多单位成本与未知 | tokens/cache/reasoning、字符/时长/请求固定fixture可复算；子集不重计；缺字段/价格保留null；0仅代表已核实零 | S02/S04 |
| U18 | 批计划与唯一重试owner | SDK/框架重试退出；每次真实请求有attempt/预算/usage；批失败保留已发生费用；不得拼接跨模型流 | S03/S04 |
| U19 | 幂等、恢复与配置漂移 | 同key同输入读原结果，异输入冲突；发送未知不盲重发；旧owner不能新发送；历史价格/模型快照保留 | S04 |
| U20 | 共享预算/配额故障 | 两副本争用不过度准入；DB/Redis故障停止新付费派发；permit/hold补偿与unknown可恢复 | S04 |
| U21 | 取消/流截断/账单迟到 | 执行与费用状态分开，unknown不归0；重复观察幂等；迟到回执/账单追加调整、聚合残差不造逐调用账 | S03/S04 |
| U22 | 容量/公平性/背压 | 固定拓扑与工作负载测50/200/500阶梯；队列/缓冲有界，慢音频/热点租户不无限耗内存 | S04后 |
| U23 | 存量迁移与回滚 | 已迁移集合无requests/SDK旁路；兼容返回形状有清单；回滚只影响新请求，不重发在途未知调用 | S03/S10 |

具名真实测试记录provider实例、model/type、协议/adapter revision、时间/限额、请求结果摘要、usage/价格来源与未知项，密钥不入回执。未配置能力标unsupported；第二厂商无凭据时仅做fake合同，不能声称真实多厂商互通。某Embedding集成只返回向量时，必须补usage-aware观察或保留缺证，不能把on_llm_end推广为六类统一账单采集器。

## 3. 性能验证口径

先用同拓扑、同请求形状的可控async stub与原生integration测封装差分，区分平台新增延迟与供应商TTFT。再按能力测试短/长LLM流、批Embedding、Rerank、音频、热点租户和慢消费；固定模型/配置、输入长度分布、机器/进程/连接/DB/Redis、tracing开关、供应商RPM/TPM与随机种子。

记录admission_wait、预算事务、TTFT、总时长/分位数、CPU/线程、峰值内存、queue/inflight/buffer、取消清理、公平等待、usage完整率、unknown/unpriced、hold age与账本lag。RPS区分受理/真实派发/成功；token/s区分单流生成和平台聚合；音频秒/向量数单列。idle SSE不算活跃模型请求，HTTP200不证明业务或容量。

没有数据的项保留null/not_run，不填0或虚构TPS。候选并发阶梯不是产品承诺；目标SLO要结合实际环境和额度确定。业务质量另用业务样本和评价规则，不由Schema/速度测试代替。

## 4. 本轮实际完成与证明限制

完成本专题重写、当前lib_request核心源码回读、DeepSeek/Dify/LangChain关键接口核对，保留旧稿并生成来源hash、图源/正文一致性和本轮写集回执。实际结果以 [design-validation.json](design-validation.json) 和 [重写复盘](../run-01/rewrite-01/03-review.md) 为准。

前轮三个LangChain离线机制观察只证明默认async可能线程fallback、usage chunk可相加、模型完成后结构化仍可失败；本轮未重跑，不代表ModelService/Bridge已实现。设计样例仅做JSON/语法与语义自审，没有导入未实现的API运行。

未执行新平台单测、六类真实provider、负载/并发、持久预算/账务/故障、生产或业务实验。Mermaid只核对图源与正文，未渲染/视觉验收。主方案方向已经确认，本轮不再次将其列为待决；各能力实装按M1–M6分片验收。

## 5. 实施前仍需明确的输入

| 输入 | 当前边界 | 对实施的影响 |
|---|---|---|
| 各能力provider/模型与可用凭据 | DeepSeek聊天沿用既有选择，其他能力按类型配置；样例别名不是已发布模型 | 逐能力选择并验证，不宣称DeepSeek一个具体模型覆盖六类 |
| 价格与用户收费 | 来源/单位/revision须核实；customer charge默认disabled | 不把示例价格或缺usage当实账，商业规则另定 |
| 容量/SLO/部署拓扑 | 模块可部署在Worker内，持久阶段接共享authority | 实测后确定配额/池/队列，不预填容量承诺 |
| 媒体、内容与回执保留 | 受控工件引用和最小账务事实 | 需落实对象存储、权限、清理和保留期限 |
| 其他task范围变动 | 本专题只细化原步骤接入候选 | 若需修改其他task，按用户规则先给具体改动取得确认 |

以上输入不妨碍完成本次设计重写；没有因此扩大本轮授权到源码实施或收费实验。
