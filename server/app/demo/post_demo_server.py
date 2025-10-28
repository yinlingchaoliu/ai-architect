from typing import Any

from fastapi import FastAPI
from langchain_core.runnables import RunnableLambda
from langserve import add_routes

from app.demo.bean import RespBean, ReqBean
from app.utils.utils import json_to_dataclass,to_dict

def register_route(app:FastAPI,config:dict):
    server = PostDemo()
    path = config.get("path", "")
    add_routes(app,server.get_chain(),path=path)
    print("注册path: "+path)
    print(config)

class PostDemo:
    """POST请求示例类 - 使用dataclass处理输入输出"""
    def __init__(self):
        pass

    def handle(self, input_data: Any) -> dict:
        # 使用dataclass进行固定格式处理

        print("PostDemo")
        try:
            print(input_data)
            content = str(input_data)
            req_bean =json_to_dataclass(content, ReqBean)

            # 创建输出dataclass实例
            output = RespBean(
                response=f"收到POST请求，处理内容：{req_bean.input}",
                status="success",
                input=req_bean.input,
                name=req_bean.name
            )
            
            # 使用asdict转换为字典
            return to_dict(output)
        except Exception as e:
            error_output = RespBean(
                response=f"处理出错: {str(e)}",
                status="success",
                input=f"错误: {input_data}",
                demo="请输入json字符串"
            )
            return to_dict(error_output)
    
    def get_chain(self):
        self.chain = RunnableLambda(self.handle)
        return self.chain
    