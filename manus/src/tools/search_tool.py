# src/tools/search_tool.py
import requests
from urllib.parse import urlencode
from .base import BaseTool
from typing import List, Dict, Any

class SearchTool(BaseTool):
    """搜索工具"""
    
    def __init__(self, api_key: str = None):
        super().__init__(
            name="web_search",
            description="Search the web for information"
        )
        self.api_key = api_key
    
    async def execute(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """执行网络搜索"""
        try:
            # 这里可以使用 SerperAPI、Google Custom Search 等
            # 这里用 DuckDuckGo 作为示例
            params = {
                'q': query,
                'format': 'json',
                'no_html': 1,
                'skip_disambig': 1
            }
            
            response = requests.get(
                'https://api.duckduckgo.com/',
                params=params,
                timeout=10
            )
            
            data = response.json()
            
            results = []
            # 提取主要结果
            if 'Abstract' in data and data['Abstract']:
                results.append({
                    "title": "Abstract",
                    "snippet": data['Abstract'],
                    "url": data['AbstractURL'] if 'AbstractURL' in data else ""
                })
            
            # 提取相关主题
            for topic in data.get('RelatedTopics', [])[:max_results]:
                if 'Text' in topic:
                    results.append({
                        "title": topic.get('FirstURL', '').split('/')[-1] if 'FirstURL' in topic else "Result",
                        "snippet": topic['Text'],
                        "url": topic.get('FirstURL', '')
                    })
            
            return {
                "success": True,
                "query": query,
                "results": results
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }