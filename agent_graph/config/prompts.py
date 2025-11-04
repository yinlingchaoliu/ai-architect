# config/prompts.py
AGENT_PROMPTS = {
    "analyzer": {
        "system": """你是专业的需求分析师...""",
        "reflection": """基于讨论进展，请重新审视最初的需求分析..."""
    },
    "moderator": {
        "system": """你是专业的会议主持人...""",
        "guidance": """当前讨论需要引导方向..."""
    }
}