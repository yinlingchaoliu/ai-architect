import os
from fastmcp import FastMCP
import math

SERVER_NAME = "MathTools"
# 初始化FastMCP服务器
mcp = FastMCP(SERVER_NAME)

@mcp.tool(description="执行数学计算")
async def calculator(expression: str) -> str:
    """执行数学计算

    Args:
        expression: 数学表达式，如 '2 + 3 * 4'

    Returns:
        计算结果
    """
    try:
        allowed_names = {"__builtins__": None}
        result = eval(expression, allowed_names, {"math": math})
        return f"计算结果: {expression} = {result}"
    except Exception as e:
        return f"计算错误: {str(e)}"

@mcp.resource("server://info")
async def server_info():
    """服务器信息资源"""
    return {
        "name": SERVER_NAME,
        "version": "1.0.0",
        "description": "数学计算",
        "tools": ["calculator"]
    }

"""
"stdio"  本地进程间通信  C-S在同一台机器
"sse"    服务端推送数据给客户端
"streamable-http" http
"""
if __name__ == "__main__":
    # 初始化并运行服务器
    # 启动服务器（Streamable HTTP，新客户端使用 /mcp）
    transport = os.getenv("MCP_TRANSPORT", "http")
    if transport == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport=transport, host=os.getenv("MCP_HOST", "127.0.0.1"),
                port=int(os.getenv("MCP_PORT", "8001")))