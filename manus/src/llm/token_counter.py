# src/llm/token_counter.py
import tiktoken
from typing import List, Dict, Any


class TokenCounter:
    """Token计数器"""

    def __init__(self):
        self.encoders = {}

    def get_encoder(self, model: str) -> tiktoken.Encoding:
        """获取编码器"""
        if model not in self.encoders:
            try:
                self.encoders[model] = tiktoken.encoding_for_model(model)
            except KeyError:
                # 默认使用 cl100k_base
                self.encoders[model] = tiktoken.get_encoding("cl100k_base")
        return self.encoders[model]

    def count_tokens(self, text: str, model: str = "gpt-4") -> int:
        """计算文本的token数量"""
        encoder = self.get_encoder(model)
        return len(encoder.encode(text))

    def count_message_tokens(self, messages: List[Dict[str, Any]], model: str = "gpt-4") -> int:
        """计算消息列表的token数量"""
        encoder = self.get_encoder(model)

        tokens_per_message = 3  # 每条消息的开销
        tokens_per_name = 1  # 名称的开销

        token_count = 0
        for message in messages:
            token_count += tokens_per_message
            for key, value in message.items():
                token_count += len(encoder.encode(str(value)))
                if key == "name":
                    token_count += tokens_per_name

        token_count += 3  # 回复的开销
        return token_count


# 全局Token计数器实例
token_counter = TokenCounter()