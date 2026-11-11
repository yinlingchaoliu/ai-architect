# 反思与后续

本轮依据真实失败和回执归纳；不将机制通过等同于业务收益或平台完成。

## 1. 有效的做法

先保存工作区基线、核对当前发布和依赖交集，再分组安装，成功暴露旧 requirements 自身不可求解和 LangServe/MCP SSE 硬冲突。三个环境保留最新核心包，避免用旧适配器限制新能力。精确锁、实装清单、pip check、协议和真实模型分别留证，使复现与结论边界可核对。

用 fake 模型驱动真实图、MCP 和 SQLite，能稳定暴露状态被丢弃、循环导入、嵌套 schema 丢失、只读限制等问题；随后真实 DeepSeek 验证将“框架机制通过”推进到“此 provider 有限兼容通过”。这种顺序减少外部调用，同时保留真实覆盖。

## 2. 需要纠正的做法

- 新 API 示例不能直接照搬旧用法：async v3 最终输出是 await stream.output()，stdio 自定义 env 需要显式传递，现代 MCP 等待输入需要 InputRequiredResult guard/return。先用最小例子对齐锁定版本，再扩展入口。
- 对配置是否受版本控制不能只看 status 或文件名。首次处理 .env 时判断错误，已恢复受控文件、迁移 .env.local、调整加载优先级并扫描新凭据。后续先用 git ls-files、读集和忽略规则确认落点。
- 计划中的“稳定”标签必须复核运行警告；v3 streaming 也被实现标为 experimental。主包稳定、API 可用、行为验证和生产成熟度分别记录。
- 旧测试引用不存在的 DiscussionSession，不能靠迁就失效测试认定兼容。应针对实际 SessionManager 公共行为，并保留历史失败与替换原因。

## 3. 保留的成本和限制

环境隔离增加安装与启动管理成本，但当前 upstream 约束无法在单环境满足。后续服务划分需消费本轮隔离事实；本轮不擅自重写其他 task。classic/community/experimental 和 PyPDF2 仍有维护风险，退出工作由既定后续阶段逐模块承担。

实际 usage 只保留已观测值，不推算全轮费用和吞吐。真实冒烟使用非思考模式，不推断思考工具链的 reasoning_content 往返兼容；持久 checkpoint、全局池解耦和完整模型路由也未提前宣布完成。

## 4. 向后续步骤交付的输入

- S02/S03：消费最终依赖组、新 Agent API、MCP schema/等待输入事实，以及主要文本模型环境配置；平台资源/身份 port 仍需正式设计。
- S04：消费内存 interrupt/resume 的机制测试，继续验证数据库持久化、重启、幂等、取消与副作用对账。
- S06/S08/S09：复用 create_agent 和 StateGraph；不能把本轮旧样例回归当作四种协作策略已落地。
- S10：按既有计划迁移旧 UI/RAG/SQL 消费；真实 Embedding、浏览器和专用模型单独验收。

以上只是 S01 的交付说明，不修改上述 task 方案。下一次执行前按最终锁、源码 hash 和当前外部版本重新核验；有必要调整其他 task 时，先提交明确变更供用户确认。
