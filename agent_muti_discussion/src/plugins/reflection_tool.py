from typing import Dict, List, Any
from .base_plugin import BasePlugin


class ReflectionToolPlugin(BasePlugin):
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.reflection_prompts = {
            "contradiction": "你刚才的观点与其他专家的观点存在矛盾，请重新思考并澄清你的立场。",
            "uncertainty": "你表达了一些不确定性，能否提供更具体的证据或数据来支持你的观点？",
            "assumption": "你的观点基于某些假设，请明确这些假设并验证其合理性。",
            "completeness": "你的分析似乎不够全面，请考虑其他可能的角度或因素。"
        }

    async def execute(self, reflection_type: str, context: Dict[str, Any] = None) -> str:
        """生成反思提示"""
        base_prompt = self.reflection_prompts.get(reflection_type, "请重新思考你的观点。")

        if context:
            # 添加上下文相关的具体问题
            specific_issue = context.get('specific_issue', '')
            if specific_issue:
                base_prompt += f"\n具体来说：{specific_issue}"

        return base_prompt

    async def analyze_for_reflection(self, text: str, history: List[Dict]) -> Dict[str, Any]:
        """分析文本是否需要反思"""
        # 简单的关键词分析，实际应该使用更复杂的NLP技术
        triggers = {
            "contradiction": ["但是", "然而", "矛盾", "不同意"],
            "uncertainty": ["可能", "也许", "不确定", "不太清楚"],
            "assumption": ["假设", "如果", "前提是"],
            "completeness": ["一方面", "部分", "某些角度"]
        }

        analysis = {"needs_reflection": False, "types": []}

        for reflection_type, keywords in triggers.items():
            if any(keyword in text for keyword in keywords):
                analysis["needs_reflection"] = True
                analysis["types"].append(reflection_type)

        return analysis