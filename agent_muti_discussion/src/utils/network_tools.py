import aiohttp
import asyncio
from typing import Dict, Any, Optional

class NetworkTools:
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None

    async def get_session(self) -> aiohttp.ClientSession:
        """获取或创建aiohttp会话"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout))
        return self.session

    async def close_session(self):
        """关闭会话"""
        if self.session and not self.session.closed:
            await self.session.close()

    async def make_request(self, url: str, method: str = "GET", headers: Dict = None, data: Dict = None) -> Dict[str, Any]:
        """发送HTTP请求"""
        session = await self.get_session()
        try:
            async with session.request(method=method, url=url, headers=headers, json=data) as response:
                return {
                    "status": response.status,
                    "content": await response.text(),
                    "headers": dict(response.headers)
                }
        except Exception as e:
            return {"error": str(e)}

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close_session()