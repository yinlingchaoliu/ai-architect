from typing import Dict, Any, List
from ..utils.network_tools import network_tools
from ..utils.logger import logger


class WebSearchPlugin:
    """网页搜索插件"""

    def __init__(self):
        self.name = "web_search"
        self.description = "搜索最新的网页信息和知识"

    def search(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """执行网页搜索"""
        try:
            logger.info(f"执行网页搜索: {query}")
            result = network_tools.search_web(query, max_results)

            if result["success"]:
                formatted_results = self._format_search_results(result["results"])
                return {
                    "success": True,
                    "results": formatted_results,
                    "summary": f"找到 {len(formatted_results)} 个相关结果"
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "搜索失败")
                }
        except Exception as e:
            logger.error(f"网页搜索异常: {str(e)}")
            return {
                "success": False,
                "error": f"搜索异常: {str(e)}"
            }

    def _format_search_results(self, results: List[Dict]) -> List[Dict]:
        """格式化搜索结果"""
        formatted = []
        for result in results:
            formatted.append({
                "title": result.get("title", ""),
                "content": result.get("snippet", ""),
                "source": result.get("url", ""),
                "relevance": "high"  # 可以添加相关性评估
            })
        return formatted

    def get_tool_description(self) -> str:
        """获取工具描述"""
        return "使用此工具搜索最新的网页信息、技术文档和市场数据"