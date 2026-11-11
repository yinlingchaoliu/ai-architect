# 思考：判断依据与取舍

本记录保存可观察的依据、决定和权衡，不记录模型内部隐含推理。

## 授权与范围

- 用户已要求执行 S01：先升级最新稳定版、采用新版能力、验证兼容并更新重要文档。S02–S11 不在本轮实施范围。
- 用户确认渐进式披露：其他 task 仅链接 `01-langchain-upgrade.md`；该入口再接入步骤目录。其他 task 保持执行前字节，仅进行批准的链接路径替换，见 `evidence/other-task-scope-check.json`。
- 所有 S01 方案补充、思考、行动、复盘、反思和证据保存在本目录树。用户指定真实模型为 deepseek-flash，凭据只保存于本地私密配置。

## 版本与隔离

版本同时核对 PyPI 稳定发布、依赖求解、精确锁、实际安装与行为结果。最终采用 LangChain 1.5.0、core 1.8.0、LangGraph 1.2.20、provider 1.7.4、OpenAI SDK 3.49.0、FastMCP 4.1.8、MCP 2.3.0；Python 3.12.15。

实际 resolver 证实 LangServe server extra 要求 sse-starlette<2，MCP 2.3 要求 >=3。采用三个独立环境，所有环境保持同一最新 LangChain/core/graph/provider，保留 UI 兼容组，避免强装冲突。旧会议 requirements 自身存在 core/graph 精确版本冲突，旧组可重建基线未成立，保留失败证据。

## 新能力的最小切片

优先验证 create_agent、middleware、ToolStrategy、content blocks、ToolRuntime/context、同步/异步 v3 events、内置 MCPAdapter、内存 checkpoint/interrupt-resume。真实 MCP 协议与确定性 fake 模型组合先验证机制，再用用户指定模型完成文本、流式、结构化输出和 HTTP MCP 工具闭环。持久数据库、平台身份、租约、四种协作策略和完整 ModelRouter 行为仍属于既定后续步骤。

上游主包稳定并不表示所有接口稳定：MCPAdapter 标 beta，v3 streaming 在实际实现中产生 experimental 警告，ModelRouter 只做 API 可用性核对，不声称生产路由通过。DeepSeek 本轮选择非思考 Chat Completions + ToolStrategy，不推断为 Responses、思考模式或严格 provider JSON Schema 已验证。

## 必要兼容修正

- 新版图只保留已声明状态字段；Manus 丢失 current_subtask 导致重复运行，补字段并给图步数设上限。
- 多个独立样例共享顶层 src 命名会相互污染；改为项目限定命名空间，并验证 editable 安装在仓库外导入。
- 讨论系统循环导入和日志目录缺失属于既有问题，阻止当前 SDK 回归；在本步最小修正。
- MCP 2 采用新的 schema 属性和 input-required 等待输入协议；保留嵌套约束和资源，避免只验证成功返回的字符串。
- CSV 使用 ChatOpenAI 适配用户指定聊天模型；旧 SQL 链只读连接有拒绝写入负例。复杂业务失败状态不借本轮升级一并重做。

## 配置处理纠正

初次把已有 `.env` 当作未跟踪配置写入，随后用 git ls-files 核对发现它们实际受控，已纠正。两份文件恢复执行前原字节，新凭据迁至被忽略、权限 0600 的 `.env.local`；加载器本地配置优先、显式进程环境优先。SDK 调试不再输出 api_key。最终扫描新凭据未出现在交付写集中。
