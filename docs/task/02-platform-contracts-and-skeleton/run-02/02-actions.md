# 行动

1. 读取批准设计与当前调用入口，固定 baseline 和现有依赖。
2. 创建 run-02，开始实现 lib_llm 和 lib_request 适配。
3. 编写 contracts/config/provider/runtime/governor/stream/sync/chat_model/compat；将已有接口接入同一 Runtime，补充包 README 与本地 editable 依赖。第三方版本保持根 requirements 基线。
4. 补充 wire、并发、公平、取消、预算、profile、原生 Agent、流式、配置边界和真实本地 HTTP/SSE 测试；将 S01 中直连 requests 的旧内部 mock 改为公共客户端 + Runtime 注入，保留对实际模型字段和凭据日志的断言。
5. 按失败证据修正：异步 callback manager 无 get_child；排队取消错误旋转租户顺序；Graph 隐式 messages 流在 run_manager=None 时重复 token；最终回归包含对应测试。历史日志保留，不能用早期失败覆盖最终结论。
6. 在根 `.venv` 重新安装两个本地包，检查依赖；只增加根 `-e ./lib_llm`，没有新增子模块虚拟环境或第三方版本变更。安装路径见 install.log，检查见 pip-check.log/installed-packages.json。
7. 使用已有、获准的 `deepseek-flash` 配置执行有限真实验证；最终候选一次三项：lib_request 文本、流式、结构化。每请求 max_attempts=1、输出 cap=64、总超时 30 秒。回执只保留状态、usage、连接池和源码指纹；不保存密钥/正文/私有 reasoning。
8. 补齐分析、思考、复盘、反思和回滚说明；回读源码/设计哈希、候选真实回执、测试 XML、写集及文档链接，保留工作区外部变化。

## 可重现命令

在仓库根执行，证据均进入当前 evidence 目录：

```bash
.venv/bin/python -m pip install --no-deps -e ./lib_llm -e ./lib_request
.venv/bin/python -m pip check
.venv/bin/python -m pytest lib_llm/tests tests/test_environment_installation.py tests/s01/test_ui_rag.py -q -o asyncio_default_fixture_loop_scope=function --junitxml=docs/task/02-platform-contracts-and-skeleton/run-02/evidence/tests.xml
```

真实验证脚本 [live-smoke.py](evidence/live-smoke.py) 会访问已配置的官方 DeepSeek 服务并产生用量，不能视为无网络测试。它只允许 deepseek-flash/api.deepseek.com；最终 [live-model.json](evidence/live-model.json) 记录当前候选。开发期间有多轮同类小额冒烟，最终回执仅覆盖最终三请求，无法由此推算本会话总费用，费用与生产 TPS 均为 UNKNOWN。

最终 [verification.json](evidence/verification.json) 是机械核验；语义与证明限制见复盘。原始上游 warning 和历史失败日志保留，不修改为“全程通过”。
