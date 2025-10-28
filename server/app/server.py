#!/usr/bin/env python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.init import DynamicRouteRegistry
from app.routes.routes_config import ROUTE_CONFIGS

app = FastAPI(
    title="LangChain 服务器",
    version="1.0",
    description="langchain 支持路由扩展",
)

route_registry = DynamicRouteRegistry(app)
route_registry.register_from_config(ROUTE_CONFIGS)

# 添加健康检查端点
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "registered_routes": route_registry.get_registered_routes()
    }

# 添加路由信息端点
@app.get("/routes")
async def get_routes():
    return {
        "route_configs": ROUTE_CONFIGS,
        "registered_routes": route_registry.get_registered_routes()
    }

# 设置所有启用 CORS 的来源
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8008)