

## 项目安装
```shell
uv init mcp-weather
```


## 配置桌面版
```json
{
    "mcpServers": {
        "weather": {
            "command": "uv",
            "args": [
                "--directory",
                "ABSOLUTE_PATH_PLACEHOLDER",
                "run",
                "main.py"
            ]
        }
    }
}
```