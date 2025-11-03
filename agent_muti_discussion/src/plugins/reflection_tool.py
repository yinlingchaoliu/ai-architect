from typing import Dict, Any, List
from ..utils.logger import logger


class ReflectionToolPlugin:
    """反思工具插件"""

    def __init__(self):
        self.name = "reflection_tool"
        self.description = "帮助智能体进行自我反思和观点调整"

    def reflect(self, current_opinion: str, other_opinions: List[str]) -> Dict[str, Any]:
        """基于其他观点进行反思"""
        try:
            logger.info("执行反思过程")

            # 分析观点差异
            differences = self._analyze_differences(current_opinion, other_opinions)

            # 生成反思结果
            reflection_result = {
                "original_opinion": current_opinion,
                "considered_alternatives": other_opinions,
                "key_differences": differences,
                "suggested_adjustments": self._suggest_adjustments(differences),
                "confidence_level": self._assess_confidence(differences)
            }

            return {
                "success": True,
                "reflection": reflection_result
            }
        except Exception as e:
            logger.error(f"反思过程异常: {str(e)}")
            return {
                "success": False,
                "error": f"反思异常: {str(e)}"
            }

    def _analyze_differences(self, current: str, others: List[str]) -> List[Dict[str, str]]:
        """分析观点差异"""
        differences = []
        for i, other in enumerate(others):
            # 简化的差异分析（实际应该使用更复杂的方法）
            if len(current) > 100 and len(other) > 100:
                # 这里可以添加更复杂的文本比较逻辑
                differences.append({
                    "expert": f"Expert_{i + 1}",
                    "difference_type": "perspective",  # 可以是perspective, evidence, conclusion等
                    "description": f"观点角度存在差异"
                })
        return differences

    def _suggest_adjustments(self, differences: List[Dict]) -> List[str]:
        """建议调整"""
        adjustments = []
        for diff in differences:
            if diff["difference_type"] == "perspective":
                adjustments.append("考虑从多个角度综合分析问题")
            elif diff["difference_type"] == "evidence":
                adjustments.append("验证和补充相关证据")
        return adjustments if adjustments else ["保持原有观点，但考虑其他专家的建议"]

    def _assess_confidence(self, differences: List[Dict]) -> str:
        """评估置信度"""
        if not differences:
            return "high"
        elif len(differences) <= 2:
            return "medium"
        else:
            return "low"

    def get_tool_description(self) -> str:
        """获取工具描述"""
        return "使用此工具基于其他专家的观点进行自我反思和观点调整"