# LangServe 服务

本服务使用仓库统一的 Python 3.12 `.venv`。依赖及本地包全部从仓库根 `requirements.txt` 安装：

```bash
# 在仓库根目录执行
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip check
```

配置文本模型所需环境变量后，从仓库根目录启动：

```bash
python -m uvicorn app.server:app --app-dir server --port 8001
```

- 健康检查：`http://localhost:8001/health`
- API 文档：`http://localhost:8001/docs`
- Playground：`http://localhost:8001/openai/playground/`

依赖修改统一维护根 `requirements.txt`。当前 venv 流程不需要安装 LangChain CLI 或 Poetry。`pyproject.toml`、`poetry.lock`、Dockerfile 保留为原独立工程材料，不作为当前统一 venv 的安装入口。

离线验证使用 fake 模型，不调用外部模型：

```bash
python -m pytest tests/s01/test_langserve.py -q
```
