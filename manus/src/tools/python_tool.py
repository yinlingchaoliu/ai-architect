# src/tools/python_tool.py
import subprocess
import sys
import tempfile
import os
from typing import Any, Dict

from .base import BaseTool

class PythonExecuteTool(BaseTool):
    """Python代码执行工具"""
    
    def __init__(self):
        super().__init__(
            name="execute_python",
            description="Execute Python code in a safe environment and return the result"
        )
    
    async def execute(self, code: str, timeout: int = 30) -> Dict[str, Any]:
        """执行Python代码"""
        try:
            # 创建临时文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            # 在子进程中执行
            result = subprocess.run(
                [sys.executable, temp_file],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            # 清理临时文件
            os.unlink(temp_file)
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Execution timeout after {timeout} seconds"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

