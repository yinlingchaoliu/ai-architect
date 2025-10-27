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

[webui](webui) : python编写界面
[ai服务](server): 提供restful api
[rag外接知识库](rag): 提供rag扩展

baselib库
1) 原则: 项目sdk之间要隔离
2) 以lib_开头
3) [基础库sdk管理](lib_hello/README.md)

[chatbot-app](webui-chatbot): 初版chat代码
从界面混合，改成MVC -> 前后端分离

chatbot + server(restful) + rag + openmanus + mcp + function_call 

先尝试封装 复用
```shell
# 基础封装 
pip install -e lib_request
```

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

## 启动项目

### chatbot-app 模块
```shell
# 启动项目
sh port.sh 1234
streamlit chatbot-app/src/home.py --server.port 1234
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
