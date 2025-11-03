import uuid
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from .base_agent import BaseAgent
from .consensus_checker import ConsensusChecker
from ..utils.logger import default_logger
from ..agents.analyzer_agent import AnalyzerAgent


class DiscussionSession:
    def __init__(self, session_id: str, moderator: BaseAgent, experts: List[BaseAgent]):
        self.session_id = session_id
        self.moderator = moderator
        self.experts = experts
        self.discussion_history = []
        self.consensus_checker = ConsensusChecker()
        self.is_active = False
        self.start_time = None
        self.end_time = None

    def _add_to_history(self, speaker: str, content: str, metadata: Dict[str, Any] = None):
        """添加讨论记录到历史"""
        entry = {
            'speaker': speaker,
            'content': content,
            'metadata': metadata or {},
            'timestamp': datetime.now().isoformat(),
            'round': len([h for h in self.discussion_history if h.get('speaker') == 'moderator'])
        }
        self.discussion_history.append(entry)
        default_logger.info(f"{speaker}: {content[:100]}...")  # 日志记录前100个字符

    def _get_current_context(self) -> str:
        """获取当前讨论上下文"""
        if not self.discussion_history:
            return "初始讨论开始"

        # 返回最近几条讨论的摘要
        recent_entries = self.discussion_history[-5:]
        context = "最近的讨论：\n"
        for entry in recent_entries:
            speaker = entry['speaker']
            content_preview = entry['content'][:50] + "..." if len(entry['content']) > 50 else entry['content']
            context += f"{speaker}: {content_preview}\n"
        return context

    async def start_discussion(self, user_prompt: str, max_rounds: int = 10) -> str:
        """开始讨论流程"""

        self.is_active = True
        self.start_time = datetime.now()
        default_logger.info(f"开始讨论会话 {self.session_id}, 用户问题: {user_prompt}")

        try:
            # 1. 分析阶段
            analyzer = AnalyzerAgent()
            analysis_result = await analyzer.process(user_prompt)
            self._add_to_history("analyzer", analysis_result.content, analysis_result.metadata)

            # 2. 提交给主持人
            moderator_response = await self.moderator.process(
                analysis_result.content,
                context={'discussion_history': self.discussion_history}
            )
            self._add_to_history("moderator", moderator_response.content, moderator_response.metadata)

            # 3. 多轮专家讨论
            round_count = 0
            # 确保discussion_history中的所有条目都是字典类型
            self.discussion_history = [entry for entry in self.discussion_history if isinstance(entry, dict)]
            
            while (round_count < max_rounds and
                   not self.consensus_checker.is_consensus_reached(self.discussion_history)):

                default_logger.info(f"开始第 {round_count + 1} 轮讨论")

                for expert in self.experts:
                    try:
                        # 专家发言
                        expert_response = await expert.process(
                            self._get_current_context(),
                            context={'discussion_history': self.discussion_history.copy()}
                        )
                        # 确保响应是有效的AgentResponse对象
                        if hasattr(expert_response, 'content') and hasattr(expert_response, 'metadata'):
                            self._add_to_history(expert.name, expert_response.content, expert_response.metadata)

                            # 主持人判断是否需要干预
                            if hasattr(expert_response, 'requires_reflection') and expert_response.requires_reflection:
                                moderator_intervention = await self.moderator.process(
                                    expert_response.content,
                                    context={
                                        'discussion_history': self.discussion_history.copy(),
                                        'current_speaker': expert.name
                                    }
                                )
                                # 确保干预响应有效
                                if hasattr(moderator_intervention, 'content') and hasattr(moderator_intervention, 'metadata'):
                                    self._add_to_history("moderator", moderator_intervention.content,
                                                         moderator_intervention.metadata)
                    except Exception as e:
                        default_logger.error(f"专家 {expert.name} 处理出错: {e}")
                        # 确保discussion_history保持有效格式
                        self.discussion_history = [entry for entry in self.discussion_history if isinstance(entry, dict)]

                round_count += 1

                # 再次确保discussion_history格式正确
                self.discussion_history = [entry for entry in self.discussion_history if isinstance(entry, dict)]
                
                # 每轮结束后检查共识
                try:
                    consensus_summary = self.consensus_checker.get_consensus_summary(self.discussion_history)
                    # 检查共识摘要是否是有效的字典
                    if isinstance(consensus_summary, dict) and 'consensus_score' in consensus_summary:
                        default_logger.info(f"第 {round_count} 轮共识分数: {consensus_summary['consensus_score']:.2f}")

                        if 'consensus_reached' in consensus_summary and consensus_summary['consensus_reached']:
                            default_logger.info("达成共识，结束讨论")
                            break
                except Exception as e:
                    default_logger.error(f"共识检查出错: {e}")

            # 4. 生成最终总结
            final_summary = await self.moderator.process(
                "请基于所有讨论生成最终总结报告",
                context={'discussion_history': self.discussion_history}
            )

            self._add_to_history("moderator", final_summary.content, final_summary.metadata)

            # 5. 返回完整讨论结果
            full_discussion = self._format_final_result(final_summary.content)
            return full_discussion

        except Exception as e:
            default_logger.error(f"讨论过程中出现错误: {e}")
            return f"讨论过程中出现错误: {e}"
        finally:
            self.is_active = False
            self.end_time = datetime.now()
            duration = (self.end_time - self.start_time).total_seconds() if self.start_time else 0
            default_logger.info(f"讨论会话 {self.session_id} 结束，耗时: {duration:.2f}秒")

    def _format_final_result(self, summary: str) -> str:
        """格式化最终结果"""
        result = f"讨论会话: {self.session_id}\n"
        result += "=" * 50 + "\n"
        result += "最终总结:\n"
        result += summary + "\n\n"
        result += "讨论过程摘要:\n"

        for i, entry in enumerate(self.discussion_history, 1):
            speaker = entry['speaker']
            content_preview = entry['content'][:80] + "..." if len(entry['content']) > 80 else entry['content']
            result += f"{i}. {speaker}: {content_preview}\n"

        # 添加共识报告
        consensus_report = self.consensus_checker.get_consensus_summary(self.discussion_history)
        result += f"\n共识分析: 分数{consensus_report['consensus_score']:.2f}, "
        result += "已达成共识" if consensus_report['consensus_reached'] else "未完全达成共识"

        return result

    def get_discussion_history(self) -> List[Dict[str, Any]]:
        """获取完整的讨论历史"""
        return self.discussion_history.copy()

    def get_session_stats(self) -> Dict[str, Any]:
        """获取会话统计信息"""
        expert_contributions = {}
        for entry in self.discussion_history:
            speaker = entry['speaker']
            if speaker not in ['analyzer', 'moderator']:
                expert_contributions[speaker] = expert_contributions.get(speaker, 0) + 1

        return {
            'session_id': self.session_id,
            'total_entries': len(self.discussion_history),
            'expert_contributions': expert_contributions,
            'duration_seconds': (
                        self.end_time - self.start_time).total_seconds() if self.start_time and self.end_time else 0,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'is_active': self.is_active
        }