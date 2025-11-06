# src/llm/manager.py
import asyncio
from typing import Dict, Any, List, Optional
import openai
from openai import AsyncOpenAI
from .models import ModelConfig, TokenUsage, LLMResponse
import logging

logger = logging.getLogger(__name__)


class LLMManager:
    """LLM管理器 - 统一管理多个模型和Token计费"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.models: Dict[str, ModelConfig] = {}
        self.clients: Dict[str, Any] = {}
        self.total_usage: Dict[str, TokenUsage] = {}
        self._initialize_models()

    def _initialize_models(self):
        """初始化模型配置"""
        # 记录完整的配置结构
        logger.info(f"Full config structure: {list(self.config.keys())}")
        
        # 检查配置中是否有models键
        if "models" in self.config:
            # 直接使用根目录的models配置作为默认模型
            model_config = self.config["models"]
            
            # 确保model_config包含name字段
            model_config_with_name = {**model_config, "name": "default"}
            config_obj = ModelConfig(**model_config_with_name)
            self.models["default"] = config_obj
            self.total_usage["default"] = TokenUsage()
            
            # 初始化客户端
            if config_obj.provider == "openai":
                self.clients["default"] = AsyncOpenAI(
                    api_key=config_obj.api_key,
                    base_url=config_obj.base_url,
                    timeout=config_obj.timeout if hasattr(config_obj, 'timeout') else 30.0
                )
            # 可以扩展其他提供商，如Azure、Anthropic等
            
            logger.info("Initialized default model from root models config")
        
        # 同时也检查是否有llm配置（兼容旧配置格式）
        llm_config = self.config.get("llm", {})
        models_config = llm_config.get("models", {})
        
        for model_name, model_config in models_config.items():
            # 确保model_config包含name字段
            model_config_with_name = {**model_config, "name": model_name}
            config_obj = ModelConfig(**model_config_with_name)
            self.models[model_name] = config_obj
            self.total_usage[model_name] = TokenUsage()
            
            # 初始化客户端
            if config_obj.provider == "openai":
                self.clients[model_name] = AsyncOpenAI(
                    api_key=config_obj.api_key,
                    base_url=config_obj.base_url,
                    timeout=config_obj.timeout if hasattr(config_obj, 'timeout') else 30.0
                )
            # 可以扩展其他提供商，如Azure、Anthropic等
        
        # 为default模型添加别名指向默认模型（如果还没有默认模型）
        if "default" not in self.models:
            default_model_name = llm_config.get("default_model")
            if default_model_name and default_model_name in self.models:
                self.models["default"] = self.models[default_model_name]
        
        logger.info(f"Initialized {len(self.models)} models: {list(self.models.keys())}")

    async def generate(
            self,
            messages: List[Dict[str, Any]],
            model: str = "default",
            tools: Optional[List[Dict]] = None,
            tool_choice: Optional[str] = None,
            **kwargs
    ) -> LLMResponse:
        """生成响应"""
        if model not in self.models:
            raise ValueError(f"Model not found: {model}")

        model_config = self.models[model]
        client = self.clients[model]

        # 准备请求参数
        request_params = {
            "model": model_config.model_name,
            "messages": messages,
            "max_tokens": model_config.max_tokens,
            "temperature": model_config.temperature,
            **kwargs
        }

        if tools:
            request_params["tools"] = tools
            if tool_choice:
                request_params["tool_choice"] = tool_choice

        try:
            # 调用API
            response = await client.chat.completions.create(**request_params)

            # 计算Token和成本
            usage = self._calculate_usage(model_config, response.usage)
            self._update_total_usage(model, usage)

            # 提取内容
            content = response.choices[0].message.content or ""
            tool_calls = None
            if response.choices[0].message.tool_calls:
                tool_calls = []
                for tool_call in response.choices[0].message.tool_calls:
                    tool_calls.append({
                        "id": tool_call.id,
                        "type": tool_call.type,
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments
                        }
                    })

            return LLMResponse(
                content=content,
                model=model,
                usage=usage,
                finish_reason=response.choices[0].finish_reason,
                tool_calls=tool_calls
            )

        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise

    def _calculate_usage(self, model_config: ModelConfig, usage_data: Any) -> TokenUsage:
        """计算Token使用和成本"""
        if hasattr(usage_data, 'prompt_tokens'):
            input_tokens = usage_data.prompt_tokens
            output_tokens = usage_data.completion_tokens
        else:
            # 如果没有提供usage，则简单估算
            input_tokens = output_tokens = 0

        cost = (input_tokens * model_config.cost_per_input_token +
                output_tokens * model_config.cost_per_output_token) / 1000  # 通常按千token计费

        return TokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            cost=cost
        )

    def _update_total_usage(self, model: str, usage: TokenUsage):
        """更新总使用量"""
        if model in self.total_usage:
            self.total_usage[model].input_tokens += usage.input_tokens
            self.total_usage[model].output_tokens += usage.output_tokens
            self.total_usage[model].total_tokens += usage.total_tokens
            self.total_usage[model].cost += usage.cost

    def get_total_usage(self) -> Dict[str, TokenUsage]:
        """获取总使用情况"""
        return self.total_usage

    def reset_usage(self):
        """重置使用统计"""
        for model in self.total_usage:
            self.total_usage[model] = TokenUsage()