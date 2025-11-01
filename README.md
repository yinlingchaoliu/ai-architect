# AI项目架构 用于商业项目实战

##  1. OpenAI API HK代理

```bash
#HK代理环境，不需要科学上网
export OPENAI_API_KEY='https://api.openai-hk.com/v1'
export OPENAI_API_KEY='hk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
```
[详见.env配置](.env)

## 2. 费用计算
1 token = 4 chars

1 token = 3/4 words

1000个token 约为750英文单词 (400汉字)

## 3.环境 python env
```shell
Python 3.12.6
```

## 4.AI 项目架构

先写代码，再画架构图

方向: chatbot + server(restful) + rag + openmanus + (mcp / function_call)

目标
tips
1) 分层架构
2) 工具能力抽象 + 动态加载
3) function_call / MCP
4) agent支持 扩展 
5) 多agent
6) restful - api
7) 前后端分离
8) python WebUI
9) rag外接数据库
10) 支持监控
11) 支持项目之间隔离
12) python库 依赖管理
13) python jni c++
14) 支持本地模型
15) 基础库抽取

### 1.[webui](webui-chatbot) : python编写界面

#### 待做
[chatbot-app](webui-chatbot): 初版chat代码

从界面混合，改成MVC -> 前后端分离

### 2.[ai服务](server): 提供restful api
-[x]  1、支持动态路由注册

-[x]  2、服务健康检查 路由配置查询

-[x]  3、支持openai服务 get/post样例

-[x] 4、支持playground调试

-[x] 5、langserve 可支持 simth (需要申请key)

-[x] 6、增加[测试用例](client/client)测试用例来测试

-[x] 7、适配支持get 配置路径 服务器默认只支持post

-[x]  8、支持[shell请求](client/shell/post.sh), 实际场景只需要post

### 3.[rag外接知识库](rag): 提供rag扩展


### 4.baselib库
1) 原则: 项目sdk之间要隔离
2) 以lib_开头
3) [基础库sdk管理](lib_hello/README.md)

-[x] 1、支持依赖库(本地发布,远程发布)

-[x] 2、lib_request 对openai request简单封装 为复用做准备

-[x] 3、lib_hello 是基础库的模版代码

### 5.mcp 协议

-[x]  编写 mcp-server [天气服务](mcp_weather)

-[x]  编写 mcp-server [计算服务](mcp_server_math)

-[x]  编写 mcp-client-manager [mcp客户端管理,支持LLM自主选择 远程MCP tools](mcp_client_manager)

-[x]  编写 mcp-client-manager 支持动态注册 mcp server

-[x]  编写 mcp-client-manager 实现 LLM 自主决策 调用与实现隔离

-[x]  编写 mcp-client-manager 增加mcp_manager 中间层 用于管理mcp服务 ,给LLM提供tools和调用

-[x]  模型支持调用工具链, 也可以自主回复

本地引用
```shell
# 基础封装 
pip install -e lib_request
```


## 启动项目

### webui-chatbot 模块
```shell
# 启动项目
sh port.sh 1234
streamlit run webui-chatbot/src/home.py --server.port 1234
```

### server 模块

```shell
# 启动项目
sh port.sh 8008
cd server
langchain serve --port 8008
cd ..
```

```shell
#查询路由表
http://127.0.0.1:8008/routes
#健康检查
http://127.0.0.1:8008/health
```

get请求
```shell
curl -X GET "http://127.0.0.1:8008/get-example/invoke?input=123"
```

post请求
```shell
curl -X POST -H "Content-Type: application/json" -d '{"input":"测试Pydantic处理"}' http://127.0.0.1:8002/post-example/invoke
```

### 通过脚手架 项目工程化
```shell
langchain app new app

pip install poetry
poetry add langchain-openai

poetry run langchain serve --port=8000
```

http://localhost:8000/openai/playground

## git问题
下次 Git 接触时 CRLF 将被 LF 替换
```shell
git config --global core.autocrlf false
```
