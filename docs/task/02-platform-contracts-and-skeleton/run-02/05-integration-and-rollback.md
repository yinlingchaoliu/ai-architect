# 接入、配置与回滚

## 本轮可用入口

新代码使用显式 Runtime 生命周期；Graph/Agent 只拿原生模型视图：

```python
from langchain.agents import create_agent
from lib_llm import LLMRuntime

async def main():
    async with LLMRuntime.from_env() as llm:
        response = await llm.generate("你好")
        print(response.message.text)
        agent = create_agent(model=llm.chat_model(), tools=[])
        result = await agent.ainvoke({"messages": [("user", "你好")]})
        return result
```

结构化：`parsed, response = await llm.structured(Schema, input)`。流式：

```python
async with llm.stream("你好") as stream:
    async for chunk in stream:
        print(chunk.text, end="")
    response = await stream.result()
```

旧同步入口保持 `OpenAIAssistantClient().request(text)`，详见 [lib_request](../../../../lib_request/README.md)。应用退出时关闭默认 Runtime；显式注入者统一管理关闭，客户端本身不关闭共享资源。同步调用不能运行在 Runtime owner loop 内，异步服务必要时 `asyncio.to_thread` 调旧入口，或直接使用 llm.achat。

## 配置管理

根项目 `.env.local` / `.env` 只由 lib_llm 装配读取；进程环境 > `.env.local` > `.env`，不写回进程环境。配置项只在 [lib_llm README](../../../../lib_llm/README.md) 维护，lib_request 不另建环境加载器。配置快照在构造 Runtime 时固定；环境文件变化需重建 Runtime。无 import 时读取、联网或实例创建。

聊天默认 `deepseek-flash`，DeepSeek 为非思考模式。embedding、vision、catalog 各有明确 profile；不能把文本模型当向量端点。密钥不写入源码、日志、执行记录或示例；不同 host 必须显式提供对应凭据。

动态配置通过可信装配方构造 ModelProfile 并 `register_profile(profile, expected_revision=old_revision)`；revision 不可原地修改，已绑定模型保留旧版本。当前是进程内配置注册，非多副本控制面同步。

## 安装与兼容

复用根 Python 3.12 `.venv`，根 requirements 已加入 `-e ./lib_llm`。本轮只重新安装两个本地 editable 包并做 pip check，依赖基线没有新增第三方版本。

```bash
.venv/bin/python -m pip install --no-deps -e ./lib_llm -e ./lib_request
.venv/bin/python -m pip check
```

完整首次安装继续使用根 `requirements.txt`，本轮未做全新虚拟环境重建验收。DeepSeekEmbeddingClient 由伪向量改为明确拒绝，底层敏感属性也不再暴露；迁移调用方见兼容 README。生产模式缺任一治理 port 拒绝启动，不能直接切 production 后假定具备共享额度。

## 回滚范围和恢复验证

起点 HEAD 见 baseline。若需回滚，先停止并关闭本轮 Runtime，保存当前工作区及最终写集；仅对审阅过的 lib_request 文件、requirements 的新增本地行、S01 受影响测试函数恢复起点内容。新建 lib_llm 文件只在确认无后续修改/消费者时按写集移除。保留 run-02 记录与已有私密配置；不要全仓 reset/clean。

隔离环境可先把上述 tracked 文件从起点 HEAD 导出到临时目录，核对内容与 Git blob 一致，确认 requirements 不再含 lib_llm 本地行。当前 [verification.json](evidence/verification.json) 的 rollback_restore 仅证明此离线恢复步骤成功，未在当前工作区执行回滚，也未模拟生产回滚。

执行期间 `.gitignore`、AGENTS.md、根/WebUI README 等并行改动不属于本轮回滚对象。应以最终写集区分本轮代码与其他工作；同文件出现并行修改时逐块核对，不能整文件覆盖。无数据库迁移，无服务部署，无需回滚外部状态。
