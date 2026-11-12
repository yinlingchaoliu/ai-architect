# 反思

## 发现、证据与修正

| 现象 | 可证实机制 | 本轮修正与防回归 |
|---|---|---|
| 原生异步工具调用失败 | AsyncCallbackManagerForLLMRun 无 get_child，错误假设同步/异步接口一致 | 显式构造 callback manager，测试 invoke/tools/structured；历史 first-tests.log 保留 |
| 租户公平测试失败 | 取消尾部排队任务也旋转了 tenant turn | 仅实际获得许可后推进轮转；公平/取消/溢出一起验证 |
| create_agent messages 出现 ABAB 而非 AB | Graph 隐式流式路径 `_astream` 收到 run_manager=None，内层 provider 继承上下文流式回调 | None 分支也显式 callbacks=[] + nostream；只允许外层发送公开 token，直接模型和 Graph 流均覆盖。graph-stream-diagnostic.log 保留失败证据 |
| 未发送排队调用可能留下预算预留 | 调用失败并不都等价于远端已生成；需要区分 dispatch | 未发送使用 release；已发送不确定使用 mark_unknown；结算失败 pending，不能重发生成 |
| 缺 usage/缓存子集容易被当0或重复计费 | provider 字段存在缺失与不同归一化位置 | 使用 nullable usage；缓存/推理是总量子集；尾部 usage 只结算一次 |
| 多环境别名可能把旧 key 或不同 host key 复用 | 以非空回退选值会忽略显式空覆盖；能力共用 endpoint 假设不成立 | 按“第一个已定义值”覆盖；跨 host 不借 key；catalog 独立 profile |

## 有效做法及适用范围

先做协议层 mock 与真实 LangChain 对象测试，再做本机真实 HTTP/SSE，最后执行三项有界外部调用，分别回答“契约正确”“协议/关闭正确”“当前 provider 接受请求”。三类证据不可互相替代。尤其普通 chat_model.astream 通过并不足以证明 create_agent 的隐式 messages streaming 正确。

同步兼容通过单一 portal 复用 loop 与连接，同时保留清晰关闭权；适用于现有 lib_request 阻塞调用。异步高并发服务应持有独立 async lifespan Runtime，而非跨 loop 共用默认同步单例。

无证据的数据保持 unknown：本轮未统计全会话费用，未压测生产 TPS，未验证真实视觉/embedding。多个别名共享 quota_group 的本地测试只能证明一个进程中的准入行为；生产准入还需要可信租户、共享后端和故障策略。

## 后续输入，未改其他计划

当接入服务多副本时，应实现并实测 AccessPort/BudgetPort/QuotaBackend，验证后端不可用、进程崩溃和预留恢复；当接入新模型时，按 chat/tool/structured/stream/image/embedding 分项验证；当启用 thinking+tools 时，先完成 provider replay 状态合同与真实多轮验证。

这些是后续讨论输入，未写入其他 task 方案，也未更新全局技能或记忆。若要扩大改造范围，沿用户既定确认规则先审方案。本轮复盘不自动产生后续实施授权。
