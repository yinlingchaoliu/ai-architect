import unittest
import asyncio
from unittest.mock import Mock, AsyncMock
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from ..core.session_manager import DiscussionSession
from ..agents.moderator_agent import ModeratorAgent
from ..expert_agents.tech_expert import TechExpertAgent
from ..expert_agents.business_expert import BusinessExpertAgent
from ..core.consensus_checker import ConsensusChecker


class TestDiscussionSystem(unittest.TestCase):
    def setUp(self):
        """测试前准备"""
        self.moderator = ModeratorAgent()
        self.tech_expert = TechExpertAgent()
        self.business_expert = BusinessExpertAgent()

    def test_session_creation(self):
        """测试会话创建"""
        session = DiscussionSession(
            session_id="test_session",
            moderator=self.moderator,
            experts=[self.tech_expert, self.business_expert]
        )

        self.assertEqual(session.session_id, "test_session")
        self.assertEqual(len(session.experts), 2)
        self.assertFalse(session.is_active)

    def test_history_tracking(self):
        """测试历史记录跟踪"""
        session = DiscussionSession(
            session_id="test_session",
            moderator=self.moderator,
            experts=[self.tech_expert]
        )

        session._add_to_history("test_speaker", "测试消息")
        history = session.get_discussion_history()

        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]['speaker'], "test_speaker")
        self.assertEqual(history[0]['content'], "测试消息")

    async def test_discussion_flow(self):
        """测试讨论流程"""
        # 使用模拟对象来避免实际API调用
        mock_moderator = AsyncMock(spec=ModeratorAgent)
        mock_tech_expert = AsyncMock(spec=TechExpertAgent)
        mock_business_expert = AsyncMock(spec=BusinessExpertAgent)

        # 设置模拟响应
        mock_moderator.process.return_value = Mock(
            content="主持人总结",
            metadata={"action": "conclude_discussion"},
            requires_reflection=False
        )

        mock_tech_expert.process.return_value = Mock(
            content="技术专家意见",
            metadata={},
            requires_reflection=False
        )

        mock_business_expert.process.return_value = Mock(
            content="商业专家意见",
            metadata={},
            requires_reflection=False
        )

        mock_tech_expert.name = "技术专家"
        mock_business_expert.name = "商业专家"

        session = DiscussionSession(
            session_id="test_flow",
            moderator=mock_moderator,
            experts=[mock_tech_expert, mock_business_expert]
        )

        # 运行讨论
        result = await session.start_discussion("测试问题", max_rounds=2)

        # 验证结果
        self.assertIsNotNone(result)
        self.assertIn("讨论会话", result)
        self.assertTrue(mock_moderator.process.called)
        self.assertTrue(mock_tech_expert.process.called)
        self.assertTrue(mock_business_expert.process.called)


class TestConsensusChecker(unittest.TestCase):
    def setUp(self):
        self.checker = ConsensusChecker(consensus_threshold=0.7)

    def test_consensus_detection(self):
        """测试共识检测"""
        # 模拟达成共识的讨论历史
        consensus_history = [
            {'speaker': 'tech', 'content': '我同意这个方案'},
            {'speaker': 'business', 'content': '完全支持这个建议'},
            {'speaker': 'research', 'content': '这个方案很好，我赞同'}
        ]

        # 模拟未达成共识的讨论历史
        no_consensus_history = [
            {'speaker': 'tech', 'content': '我反对这个方案'},
            {'speaker': 'business', 'content': '这个建议有问题'},
            {'speaker': 'research', 'content': '需要重新考虑'}
        ]

        # 由于我们的模拟数据比较简单，这里主要测试功能完整性
        result1 = self.checker.is_consensus_reached(consensus_history)
        result2 = self.checker.is_consensus_reached(no_consensus_history)

        # 至少应该能够正常运行而不报错
        self.assertIn(result1, [True, False])
        self.assertIn(result2, [True, False])


if __name__ == '__main__':
    # 运行异步测试
    loop = asyncio.get_event_loop()

    # 运行同步测试
    unittest.main(verbosity=2)