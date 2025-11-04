# tools/web_search.py
import aiohttp
import os
from typing import Optional


class WebSearchTool:
    def __init__(self):
        self.api_key = os.getenv("SERPAPI_KEY")

    async def search(self, query: str, num_results: int = 3) -> str:
        """使用SerpAPI进行网页搜索"""
        if not self.api_key:
            return "搜索功能未配置API密钥"

        async with aiohttp.ClientSession() as session:
            params = {
                'q': query,
                'api_key': self.api_key,
                'engine': 'google',
                'num': num_results
            }

            async with session.get('https://serpapi.com/search', params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_search_results(data)
                else:
                    return f"搜索失败: {response.status}"

    def _parse_search_results(self, data: dict) -> str:
        results = []
        if 'organic_results' in data:
            for result in data['organic_results'][:3]:
                title = result.get('title', '')
                snippet = result.get('snippet', '')
                results.append(f"{title}: {snippet}")

        return "\n".join(results) if results else "未找到相关信息"


