#!/usr/bin/env python3
"""
多智能体讨论决策系统启动脚本
"""

import os
import sys
from dotenv import load_dotenv


def setup_environment():
    """设置环境变量"""
    # 加载.env文件
    if os.path.exists('.env'):
        load_dotenv('.env')
        print("已加载环境变量文件")
    else:
        print("警告: 未找到.env文件，请确保已设置环境变量")

    # 检查必要的环境变量
    required_vars = ['OPENAI_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print(f"错误: 缺少必要的环境变量: {', '.join(missing_vars)}")
        print("请在.env文件中设置或直接设置环境变量")
        sys.exit(1)

    # 创建必要的目录
    os.makedirs('logs', exist_ok=True)
    os.makedirs('data', exist_ok=True)

    print("环境设置完成")


if __name__ == "__main__":
    setup_environment()

    # 导入并启动主程序
    from main import main

    main()