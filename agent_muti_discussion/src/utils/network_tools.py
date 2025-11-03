import requests
from typing import Dict, Any, Optional
import json


class NetworkTools:
    """网络工具类"""

    @staticmethod
    def make_request(url: str, method: str = "GET", headers: Optional[Dict] = None,
                     data: Optional[Dict] = None, timeout: int = 30) -> Dict[str, Any]:
        """发送HTTP请求"""
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return {
                "success": True,
                "data": response.json() if response.content else {},
                "status_code": response.status_code
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
            }

    @staticmethod
    def search_web(query: str, max_results: int = 5) -> Dict[str, Any]:
        """网页搜索工具（需要接入实际的搜索API）"""
        # 这里可以接入Serper、Google Search等API
        # 暂时返回模拟数据
        return {
            "success": True,
            "results": [
                {
                    "title": f"搜索结果 {i + 1} - {query}",
                    "snippet": f"这是关于 {query} 的相关信息摘要...",
                    "url": f"https://example.com/result{i + 1}"
                }
                for i in range(max_results)
            ]
        }


# 全局网络工具实例
network_tools = NetworkTools()