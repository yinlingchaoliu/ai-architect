from typing import Dict, Any, List, Optional
from ..utils.logger import logger


class ConsensusChecker:
    """一致性检查器"""

    def __init__(self):
        self.name = "consensus_checker"

    def check_consensus(self, opinions: List[Dict[str, Any]], max_differences: int = 2) -> Dict[str, Any]:
        """检查专家意见的一致性"""
        try:
            logger.info("开始一致性检查")

            if len(opinions) <= 1:
                return {
                    "consensus_achieved": True,
                    "confidence": "high",
                    "reason": "只有一个专家意见"
                }

            # 分析意见差异
            differences = self._analyze_differences(opinions)

            # 评估一致性
            consensus_result = self._evaluate_consensus(differences, max_differences)

            result = {
                "consensus_achieved": consensus_result["achieved"],
                "confidence": consensus_result["confidence"],
                "differences_found": len(differences),
                "key_differences": differences,
                "suggestions": consensus_result["suggestions"]
            }

            logger.info(f"一致性检查完成: 达成共识={result['consensus_achieved']}")
            return result
        except Exception as e:
            logger.error(f"一致性检查异常: {str(e)}")
            return {
                "consensus_achieved": False,
                "confidence": "low",
                "error": f"检查异常: {str(e)}"
            }

    def _analyze_differences(self, opinions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """分析意见差异"""
        differences = []

        for i in range(len(opinions)):
            for j in range(i + 1, len(opinions)):
                diff = self._compare_opinions(opinions[i], opinions[j])
                if diff:
                    differences.append({
                        "expert1": opinions[i].get("expert_name", f"Expert_{i}"),
                        "expert2": opinions[j].get("expert_name", f"Expert_{j}"),
                        "difference": diff
                    })

        return differences

    def _compare_opinions(self, opinion1: Dict, opinion2: Dict) -> Optional[str]:
        """比较两个专家意见"""
        content1 = str(opinion1.get("opinion", ""))
        content2 = str(opinion2.get("opinion", ""))

        # 简化的差异检测（实际应该使用更复杂的NLP方法）
        if len(content1) > 100 and len(content2) > 100:
            # 检查关键观点是否一致
            key_phrases1 = self._extract_key_phrases(content1)
            key_phrases2 = self._extract_key_phrases(content2)

            if set(key_phrases1) != set(key_phrases2):
                return "关键观点存在差异"

        return None

    def _extract_key_phrases(self, text: str) -> List[str]:
        """提取关键短语（简化版）"""
        # 这里可以集成更复杂的关键词提取算法
        words = text.lower().split()
        key_words = [word for word in words if len(word) > 3]
        return list(set(key_words))[:5]  # 返回前5个唯一关键词

    def _evaluate_consensus(self, differences: List[Dict], max_differences: int) -> Dict[str, Any]:
        """评估一致性程度"""
        if len(differences) == 0:
            return {
                "achieved": True,
                "confidence": "high",
                "suggestions": ["专家意见高度一致"]
            }
        elif len(differences) <= max_differences:
            return {
                "achieved": True,
                "confidence": "medium",
                "suggestions": ["专家意见基本一致，存在少量差异"]
            }
        else:
            return {
                "achieved": False,
                "confidence": "low",
                "suggestions": ["专家意见分歧较大，需要进一步讨论"]
            }