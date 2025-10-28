from fastapi import FastAPI,Request
from langchain_core.runnables import RunnableLambda
from langserve import add_routes

from app.demo.bean import ReqBean, RespBean
from app.server import app
from app.utils.utils import to_dict,query_string_to_dataclass,json_to_dataclass

def register_route(app:FastAPI,config:dict):
    server = GetDemo()
    server.enableJson(True)
    path = config.get("path", "")
    add_routes(app,server.get_chain(),path=path)
    print("注册path: "+path)
    print(config)

"""
增加get请求
"""
@app.get("/get_demo/invoke")
async def get_example_invoke(request: Request):
   query_str = str(request.url.query)
   print(query_str)
   demo  = GetDemo()
   return demo.get_chain().invoke(query_str)

class GetDemo:
    """GET请求示例类 - 使用Pydantic模型处理输入输出"""
    def __init__(self):
        self.is_json = False

    def enableJson(self,flag):
        self.is_json = flag

    def handle(self, input_data: str) -> dict:
        # 使用dataclass进行固定格式处理
        try:
            print("getDemo")
            print(input_data)
            content = str(input_data)
            if self.is_json:
                req_bean =json_to_dataclass(content, ReqBean)
            else :
                req_bean =query_string_to_dataclass(content, ReqBean)

            # 创建输出dataclass实例
            output = RespBean(
                response=f"收到Get请求，处理内容：{req_bean.input}",
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
                name="xxxx",
                demo="请输入json字符串"
            )
            return to_dict(error_output)   

    def get_chain(self):
        self.chain = RunnableLambda(self.handle)
        return self.chain