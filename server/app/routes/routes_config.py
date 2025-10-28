"""
基于路由配置
"""

ROUTE_CONFIGS = {
    "chat": [
        {
            "module_path": "app.chain.openai_server",
            "enabled": True,
            "path": "/openai",
            "tags": ["openai"],
            "description": "openai对话服务"
        },
        {
            "module_path": "app.chain.openai_prompt_server",
            "enabled": True,
            "path": "/openai_ext",
            "tags": ["openai_ext", "conversation"],
            "description": "智能对话服务扩展"
        }
    ],
    "rag": [
        {
            "module_path": "app.rag.rag_service",
            "enabled": False,
            "path": "/rag",
            "tags": ["rag"],
            "description": "检索增强生成服务"
        },
        {
            "module_path": "app.rag.rag_search_service",
            "enabled": False,
            "path": "/rag_search",
            "tags": ["search"],
            "description": "相似查询服务"
        }
    ],
}