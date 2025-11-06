# src/tools/file_tool.py
import json
import os
from typing import List, Dict, Any
from .base import BaseTool


class FileTool(BaseTool):
    """文件操作工具"""

    def __init__(self):
        super().__init__(
            name="file_operations",
            description="Read, write, and manage files"
        )

    async def execute(self, operation: str, path: str, content: str = None) -> Dict[str, Any]:
        """执行文件操作"""
        try:
            if operation == "read":
                with open(path, 'r', encoding='utf-8') as f:
                    return {
                        "success": True,
                        "content": f.read(),
                        "operation": "read"
                    }

            elif operation == "write":
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return {
                    "success": True,
                    "operation": "write",
                    "path": path
                }

            elif operation == "list":
                items = os.listdir(path)
                return {
                    "success": True,
                    "items": items,
                    "operation": "list"
                }

            else:
                return {
                    "success": False,
                    "error": f"Unsupported operation: {operation}"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }