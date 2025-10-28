# main.py
import asyncio
import sys
from src.config.config import MCP_SERVERS, LLM_CONFIG
from src.core.mcp_client import MCPProtocolClient
from src.core.mcp_router import LLMProtocolRouter


class MCPApplication:
    """基于MCP协议的智能应用 - 完全解耦架构"""

    def __init__(self):
        self.mcp_client = MCPProtocolClient()
        self.llm_router = LLMProtocolRouter(self.mcp_client, LLM_CONFIG["api_key"])

    async def initialize(self):
        """通过MCP协议初始化所有服务器"""
        print("🚀 初始化MCP协议系统...")

        # 通过协议注册所有服务器
        for server_name, server_url in MCP_SERVERS.items():
            await self.mcp_client.register_server(server_name, server_url)

        # 显示通过协议发现的所有工具
        tools = self.mcp_client.get_all_tool_schemas()
        print(f"✅ 系统初始化完成! 通过MCP协议发现 {len(tools)} 个工具")

        for tool in tools:
            function_info = tool["function"]
            print(f"   📌 {function_info['name']}: {function_info['description']}")

    async def run_interactive(self):
        """运行交互式会话"""
        print("\n" + "=" * 60)
        print("🤖 MCP协议智能系统 (完全解耦架构)")
        print("=" * 60)
        print("• MCP客户端通过协议动态发现工具")
        print("• LLM通过function calling决策工具调用")
        print("• 客户端与服务器完全解耦")
        print("=" * 60)
        print("输入 'quit' 退出程序")
        print("=" * 60)

        while True:
            try:
                user_input = input("\n💬 用户输入: ").strip()

                if user_input.lower() in ['quit', 'exit', '退出']:
                    print("👋 再见!")
                    break

                if not user_input:
                    continue

                # 通过LLM和MCP协议处理请求
                print("🔄 通过MCP协议处理中...")
                response = await self.llm_router.process_user_request(user_input)
                print(f"📋 系统回复:\n{response}")

            except KeyboardInterrupt:
                print("\n\n👋 程序被用户中断")
                break
            except Exception as e:
                print(f"❌ 系统错误: {e}")

    async def cleanup(self):
        """清理协议连接"""
        await self.mcp_client.close_all()


async def main():
    """主函数"""
    app = MCPApplication()

    try:
        await app.initialize()
        await app.run_interactive()
    finally:
        await app.cleanup()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # 命令行模式
        async def command_line_mode():
            app = MCPApplication()
            await app.initialize()
            user_input = " ".join(sys.argv[1:])
            response = await app.llm_router.process_user_request(user_input)
            print(response)
            await app.cleanup()


        asyncio.run(command_line_mode())
    else:
        # 交互式模式
        asyncio.run(main())