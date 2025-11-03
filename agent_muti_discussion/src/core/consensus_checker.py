from typing import List, Dict, Any
import re


class ConsensusChecker:
    def __init__(self, consensus_threshold: float = 0.8, min_agreements: int = 2):
        self.consensus_threshold = consensus_threshold
        self.min_agreements = min_agreements

    def is_consensus_reached(self, discussion_history: List[Dict]) -> bool:
        """检查是否达成共识"""
        if len(discussion_history) < 3:  # 至少需要一些讨论
            return False

        recent_discussion = discussion_history[-10:]  # 检查最近10条发言

        # 提取关键观点和立场
        viewpoints = self._extract_viewpoints(recent_discussion)

        if len(viewpoints) < self.min_agreements:
            return False

        # 计算共识度
        consensus_score = self._calculate_consensus_score(viewpoints)

        return consensus_score >= self.consensus_threshold

    def _extract_viewpoints(self, discussion: List[Dict]) -> List[Dict[str, Any]]:
        """从讨论中提取关键观点"""
        viewpoints = []

        for entry in discussion:
            content = entry.get('content', '')
            speaker = entry.get('speaker', '')

            if not content or speaker in ['analyzer', 'moderator']:
                continue

            # 提取立场和关键论点
            viewpoint = {
                'speaker': speaker,
                'stance': self._detect_stance(content),
                'key_points': self._extract_key_points(content),
                'agreement_level': self._detect_agreement_level(content)
            }
            viewpoints.append(viewpoint)

        return viewpoints

    def _detect_stance(self, text: str) -> str:
        """检测立场"""
        positive_indicators = ["支持", "同意", "建议", "推荐", "可行", "有利"]
        negative_indicators = ["反对", "不建议", "风险", "问题", "困难", "不可行"]
        neutral_indicators = ["可能", "需要考虑", "取决于", "有条件"]

        if any(indicator in text for indicator in positive_indicators):
            return "positive"
        elif any(indicator in text for indicator in negative_indicators):
            return "negative"
        elif any(indicator in text for indicator in neutral_indicators):
            return "neutral"
        else:
            return "unknown"

    def _extract_key_points(self, text: str) -> List[str]:
        """提取关键论点"""
        # 简单的论点提取，实际应该使用更复杂的NLP技术
        points = []

        # 提取编号列表
        numbered_points = re.findall(r'\d+\.\s*(.*?)(?=\d+\.|$)', text)
        points.extend(numbered_points)

        # 提取关键短语
        key_phrases = re.findall(r'[^。！？]+(?:优势|好处|风险|问题|建议)[^。！？]*[。！？]', text)
        points.extend(key_phrases)

        return points[:5]  # 返回前5个关键点

    def _detect_agreement_level(self, text: str) -> float:
        """检测同意程度"""
        strong_agreement = ["完全同意", "强烈支持", "毫无疑问"]
        moderate_agreement = ["同意", "支持", "认可"]
        weak_agreement = ["基本同意", "可以考虑", "部分支持"]

        if any(phrase in text for phrase in strong_agreement):
            return 1.0
        elif any(phrase in text for phrase in moderate_agreement):
            return 0.7
        elif any(phrase in text for phrase in weak_agreement):
            return 0.4
        else:
            return 0.0

    def _calculate_consensus_score(self, viewpoints: List[Dict]) -> float:
        """计算共识分数"""
        if not viewpoints:
            return 0.0

        # 计算立场一致性
        stances = [v['stance'] for v in viewpoints]
        positive_count = stances.count('positive')
        consensus_ratio = positive_count / len(stances)

        # 考虑同意程度
        avg_agreement = sum(v['agreement_level'] for v in viewpoints) / len(viewpoints)

        # 综合共识分数
        total_score = (consensus_ratio + avg_agreement) / 2
        return total_score

    def get_consensus_summary(self, discussion_history: List[Dict]) -> Dict[str, Any]:
        """生成共识摘要"""
        recent_discussion = discussion_history[-10:]
        viewpoints = self._extract_viewpoints(recent_discussion)

        summary = {
            'consensus_reached': self.is_consensus_reached(discussion_history),
            'consensus_score': self._calculate_consensus_score(viewpoints),
            'participating_experts': list(set(v['speaker'] for v in viewpoints)),
            'main_viewpoints': [
                {
                    'expert': v['speaker'],
                    'stance': v['stance'],
                    'key_points': v['key_points'][:2]  # 前2个关键点
                }
                for v in viewpoints
            ]
        }

        return summary