# src/tools/base.py
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
import inspect

class ToolParameter(BaseModel):
    """工具参数定义"""
    name: str
    type: str
    description: str
    required: bool = True

class ToolSchema(BaseModel):
    """工具模式定义"""
    name: str
    description: str
    parameters: list[ToolParameter]

class BaseTool(ABC):
    """基础工具抽象类"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.schema = self._generate_schema()
    
    def _generate_schema(self) -> ToolSchema:
        """自动生成工具模式"""
        execute_method = getattr(self, 'execute')
        signature = inspect.signature(execute_method)
        
        parameters = []
        for param_name, param in signature.parameters.items():
            if param_name == 'self':
                continue
                
            parameters.append(ToolParameter(
                name=param_name,
                type=str(param.annotation) if param.annotation != inspect.Parameter.empty else "str",
                description=f"Parameter {param_name}",
                required=param.default == inspect.Parameter.empty
            ))
        
        return ToolSchema(
            name=self.name,
            description=self.description,
            parameters=parameters
        )
    
    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """执行工具"""
        pass
    
    def get_schema(self) -> Dict[str, Any]:
        """获取工具模式（兼容OpenAI格式）"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        param.name: {
                            "type": param.type,
                            "description": param.description
                        } for param in self.schema.parameters
                    },
                    "required": [param.name for param in self.schema.parameters if param.required]
                }
            }
        }