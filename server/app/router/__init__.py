import os
import importlib
from fastapi import FastAPI
from langserve import add_routes

def register_all_routes(app: FastAPI):
    """动态注册所有路由[citation:7]"""
    routes_dir = os.path.dirname(__file__)

    for filename in os.listdir(routes_dir):
        if filename.endswith(".py") and filename not in ["__init__.py", "__pycache__"]:
            module_name = filename[:-3]  # 移除.py后缀
            try:
                # 动态导入路由模块[citation:7]
                module = importlib.import_module(f".{module_name}", package="app.routes")
                # 调用每个模块中的注册函数
                if hasattr(module, "register_route"):
                    module.register_route(app)
                    print(f"✅ 成功注册路由: {module_name}")
            except ImportError as e:
                print(f"❌ 导入路由模块 {module_name} 失败: {e}")
            except Exception as e:
                print(f"❌ 注册路由 {module_name} 时出错: {e}")