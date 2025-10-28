import importlib
import logging
from typing import Dict, Any, List
from fastapi import FastAPI

logger = logging.getLogger(__name__)


class DynamicRouteRegistry:
    """动态路由注册器 - 支持模块到服务列表的映射"""

    def __init__(self, app: FastAPI):
        self.app = app
        self.registered_routes = []

    def register_from_config(self, route_configs: Dict[str, List[Dict[str, Any]]]):
        """
        根据配置动态注册路由

        Args:
            route_configs: 路由配置字典，模块名到服务列表的映射
        """
        for module_name, services_config in route_configs.items():
            logger.info(f"开始注册模块: {module_name}")

            for service_config in services_config:
                if not service_config.get("enabled", True):
                    logger.info(f"跳过禁用服务: {module_name}.{service_config.get('path')}")
                    continue

                self._register_single_service(module_name, service_config)

    def _register_single_service(self, module_name: str, service_config: Dict[str, Any]):
        """
        注册单个服务

        Args:
            module_name: 模块名称
            service_config: 服务配置
        """
        module_path = service_config.get("module_path")
        if not module_path:
            logger.error(f"服务配置缺少 module_path: {service_config}")
            return

        try:
            # 动态导入模块
            module = importlib.import_module(module_path)

            # 检查模块是否有 register_route 方法
            if hasattr(module, 'register_route'):
                # 调用模块的 register_route 方法
                module.register_route(self.app, service_config)

                logger.info(f"✅ 成功注册服务: {module_name} -> {service_config.get('path')}")
                self.registered_routes.append({
                    "module": module_name,
                    "service_path": service_config.get("path"),
                    "module_path": module_path,
                    "tags": service_config.get("tags", []),
                    "description": service_config.get("description", "")
                })
            else:
                logger.warning(f"⚠️ 模块 {module_path} 没有 register_route 方法")

        except ImportError as e:
            logger.error(f"❌ 导入模块失败 {module_path}: {e}")
        except Exception as e:
            logger.error(f"❌ 注册服务 {module_name} 时出错: {e}")

    def get_registered_routes(self):
        """获取已注册的路由信息"""
        return self.registered_routes