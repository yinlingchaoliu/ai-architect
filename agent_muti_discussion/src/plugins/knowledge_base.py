from typing import Dict, Any, List
import json
import os
from ..utils.logger import logger


class KnowledgeBasePlugin:
    """知识库插件（简化版RAG）"""

    def __init__(self, knowledge_base_path: str = "data/knowledge_base.json"):
        self.name = "knowledge_base"
        self.description = "访问内部知识库和文档"
        self.knowledge_base_path = knowledge_base_path
        self.knowledge_data = self._load_knowledge_base()

    def _load_knowledge_base(self) -> Dict[str, Any]:
        """加载知识库数据"""
        try:
            if os.path.exists(self.knowledge_base_path):
                with open(self.knowledge_base_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # 返回默认知识库结构
                return {
                    "technology": {
                        "frameworks": ["LangChain", "OpenAI", "Multi-Agent"],
                        "best_practices": ["系统设计原则", "代码规范"],
                        "case_studies": []
                    },
                    "business": {
                        "models": ["SaaS", "Subscription"],
                        "metrics": ["ROI", "LTV"],
                        "strategies": []
                    }
                }
        except Exception as e:
            logger.error(f"加载知识库失败: {str(e)}")
            return {}

    def query(self, question: str, domain: str = "all") -> Dict[str, Any]:
        """查询知识库"""
        try:
            logger.info(f"查询知识库: question - 领域: {domain}")

            if domain == "all":
                # 在所有领域搜索
                results = []
                for domain_name, domain_data in self.knowledge_data.items():
                    domain_results = self._search_in_domain(question, domain_data)
                    results.extend(domain_results)
            else:
                # 在指定领域搜索
                domain_data = self.knowledge_data.get(domain, {})
                results = self._search_in_domain(question, domain_data)
            logger.info(f"返回知识库: {results} - 领域: {domain}")
            return {
                "success": True,
                "results": results,
                "count": len(results)
            }
        except Exception as e:
            logger.error(f"知识库查询异常: {str(e)}")
            return {
                "success": False,
                "error": f"查询异常: {str(e)}"
            }

    def _search_in_domain(self, question: str, domain_data: Dict) -> List[Dict]:
        """在特定领域内搜索"""
        results = []
        for category, items in domain_data.items():
            if isinstance(items, list):
                for item in items:
                    if question.lower() in str(item).lower():
                        results.append({
                            "domain": "unknown",
                            "category": category,
                            "content": item,
                            "confidence": 0.8
                        })
        return results

    def add_knowledge(self, domain: str, category: str, content: Any) -> bool:
        """添加知识到知识库"""
        try:
            if domain not in self.knowledge_data:
                self.knowledge_data[domain] = {}

            if category not in self.knowledge_data[domain]:
                self.knowledge_data[domain][category] = []

            self.knowledge_data[domain][category].append(content)

            # 保存到文件
            os.makedirs(os.path.dirname(self.knowledge_base_path), exist_ok=True)
            with open(self.knowledge_base_path, 'w', encoding='utf-8') as f:
                json.dump(self.knowledge_data, f, ensure_ascii=False, indent=2)

            logger.info(f"成功添加知识到 {domain}.{category}")
            return True
        except Exception as e:
            logger.error(f"添加知识失败: {str(e)}")
            return False

    def get_tool_description(self) -> str:
        """获取工具描述"""
        return "使用此工具查询内部知识库、技术文档和最佳实践"