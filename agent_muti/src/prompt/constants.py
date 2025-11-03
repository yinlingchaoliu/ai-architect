
"""
只有核心流程的提示词 写在这里，插件提示词 写在插件文件中
think->plan->action(None)->next  -》 循环执行 -》 summary
"""

### 解决返回```json 问题
JSON_FORMAT = """
注意: 请以JSON格式返回, 不要使用```json等代码块标记
"""

# think提示词
THINK_PROMPT = """
你是一个深思熟虑的分析专家，能够准确评估当前状况和下一步需求。
"""

def think_prompt(query, context, iteration_count) -> str:
    think_prompt = f"""
当前用户查询: {query}
历史上下文: {context}
当前迭代: {iteration_count}

请分析：
1. 用户的核心需求是什么？
2. 当前已经获得了哪些信息？
3. 还需要获取哪些关键信息？
4. 是否可以直接回答用户问题？

返回分析结果 包括：
- core_requirements: 核心需求列表
- acquired_info: 已获得信息
- missing_info: 缺失的关键信息
- confidence_level: 当前置信度(0-1)
- should_complete: 是否可以直接完成
- reasoning: 推理过程
{JSON_FORMAT}
"""
    return think_prompt


PLAN_PROMPT = """
你是一个专业的任务规划师，能够制定高效的信息收集和执行计划。
"""

def plan_prompt(query, context, missing_info, available_agents) -> str:
    plan_prompt = f"""
用户查询: {query}
缺失信息: {missing_info}
可用Agent: {available_agents}
当前上下文: {context}

请制定一个详细的执行计划来获取缺失信息：
- required_agents: 需要调用的Agent列表
- execution_sequence: 执行序列（并行/串行）
- expected_outputs: 期望从每个Agent获得的输出
- strategy: 执行策略
- iteration_goal: 本轮迭代的目标

{JSON_FORMAT}
"""
    return plan_prompt

NEXT_PROMPT = """
你是一个决策专家，能够基于当前信息质量决定是否继续迭代。
"""

def next_prompt(query, updated_context, agent_responses) -> str:
    next_prompt = f"""
原始查询: {query}
当前收集到的信息: {updated_context}
Agent执行结果: {agent_responses}

请评估：
1. 当前信息是否足够回答用户问题？
2. 是否需要继续迭代收集更多信息？
3. 下一轮迭代的重点应该是什么？

返回：
- should_terminate: 是否终止迭代
- confidence_score: 当前整体置信度(0-1)
- next_focus: 下一轮迭代重点
- reasoning: 决策理由
{JSON_FORMAT}
"""
    return next_prompt

# 总结提示词
SUMMARY_PROMPT = """
你是一个专业的整合专家，擅长将多轮迭代收集的专业信息整合成用户友好的最终回答。
"""

def summary_prompt(query, summaries, iteration_count,agent_count) -> str:
    summary_prompt = f"""
用户原始查询: {query}

经过{iteration_count}轮迭代收集，获得以下专业分析:
{summaries}

迭代过程摘要:
- 总迭代轮次: {iteration_count}
- 收集到的关键信息: {agent_count}个专业分析

请基于以上所有信息，生成一个完整、准确、有用的最终回答。
确保回答自然流畅，突出关键信息，并提供实用的建议。
"""
    return summary_prompt