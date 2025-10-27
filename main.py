#!/usr/bin/env python3
"""
主程序 - 演示如何使用本地 hello SDK
"""

import sys
import os
# 确保可以导入 hello SDK

try:
    from lib_hello import HelloClient, say_hello, format_message
except ImportError:
    print("错误: 无法导入 hello SDK")
    print("请先安装: pip install -e ./hello")
    sys.exit(1)


def demo_basic_usage():
    """演示基础用法"""
    print("=== Hello SDK 基础用法演示 ===")

    # 使用快速函数
    print(say_hello())  # Hello, World!
    print(say_hello("Alice"))  # Hello, Alice!
    print(say_hello("Bob", "es"))  # Hola, Bob!
    print(say_hello("世界", "zh"))  # 你好, 世界!

    print()


def demo_client_usage():
    """演示客户端用法"""
    print("=== Hello SDK 客户端演示 ===")

    # 创建客户端实例
    client = HelloClient("Developer")

    # 基础问候
    print(client.greet())  # Hello, Developer!

    # 带消息的问候
    print(client.greet("Welcome to our SDK!"))

    # 切换语言
    client.set_language("fr")
    print(client.greet("Comment ça va?"))

    # 查看支持的语言
    languages = client.get_supported_languages()
    print(f"支持的语言: {', '.join(languages)}")

    print()


def demo_advanced_usage():
    """演示高级用法"""
    print("=== Hello SDK 高级用法演示 ===")

    # 创建多个客户端实例
    clients = [
        HelloClient("User1", "en"),
        HelloClient("Usuario2", "es"),
        HelloClient("Utilisateur3", "fr"),
        HelloClient("用户4", "zh")
    ]

    for client in clients:
        print(client.greet("Nice to meet you!"))

    print()


def demo_utils():
    """演示工具函数"""
    print("=== 工具函数演示 ===")

    # 格式化消息
    formatted = format_message("Hello, {name}! Today is {day}.", name="John", day="Monday")
    print(formatted)

    # 验证名称
    from lib_hello.utils import validate_name
    print(f"验证 'Alice': {validate_name('Alice')}")
    print(f"验证空字符串: {validate_name('')}")

    print()


def main():
    """主函数"""
    print("Hello SDK 演示程序\n")

    try:
        demo_basic_usage()
        demo_client_usage()
        demo_advanced_usage()
        demo_utils()

        print("🎉 所有演示完成！")

    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())