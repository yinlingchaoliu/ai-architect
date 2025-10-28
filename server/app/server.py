#!/usr/bin/env python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langserve import add_routes

from .openai_prompt_server import OpenAIPromptServer
from .openai_server import OpenAIServer

app = FastAPI(
    title="LangChain 服务器",
    version="1.0",
    description="langchain 支持路由扩展",
)

openaiServer = OpenAIServer()
openaiPromptServer = OpenAIPromptServer()

add_routes(app,openaiServer.get_chain(),path="/openai")
add_routes(app,openaiPromptServer.get_chain(),path="/openai_ext")

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
    uvicorn.run(app, host="localhost", port=8005)
