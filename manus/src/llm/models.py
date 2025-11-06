# src/llm/models.py
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import tiktoken

class ModelConfig(BaseModel):
    """模型配置"""
    name: str
    provider: str  # "openai", "anthropic", "ollama", "azure"
    model_name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: int = 4096
    temperature: float = 0.0
    timeout: int = 30
    cost_per_input_token: float = 0.0
    cost_per_output_token: float = 0.0

class TokenUsage(BaseModel):
    """Token使用情况"""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost: float = 0.0

class LLMResponse(BaseModel):
    """LLM响应"""
    content: str
    model: str
    usage: TokenUsage
    finish_reason: Optional[str] = None
    tool_calls: Optional[List[Dict]] = None