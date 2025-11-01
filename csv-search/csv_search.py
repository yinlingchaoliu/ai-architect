import os
# 导入正则表达式模块
import re
import sqlite3
import pandas as pd
import streamlit as st
from llm import RetrievalLLM

# 数据文件路径
DATA_PATH = 'data'
# 数据表名称
TABLES = ('brand_category', 'categories', 'offer_retailer')
# 数据库名称
DB_NAME = 'offer_db.sqlite'
# 提示模板
PROMPT_TEMPLATE = """
                你会接收到一个查询，你的任务是从`offer_retailer`表中的`OFFER`字段检索相关offer。
                查询可能是混合大小写的，所以也要搜索大写版本的查询。
                重要的是，你可能需要使用数据库中其他表的信息，即：`brand_category`, `categories`, `offer_retailer`，来检索正确的offer。
                不要虚构offer。如果在`offer_retailer`表中找不到offer，返回字符串：`NONE`。
                如果你能从`offer_retailer`表中检索到offer，用分隔符`#`分隔每个offer。例如，输出应该是这样的：`offer1#offer2#offer3`。
                如果SQLResult为空，返回`None`。不要生成任何offer。
                这是查询：`{}`
                """

# Streamlit应用标题
st.title("搜索offer 🔍")

# 连接SQLite数据库
conn = sqlite3.connect('offer_db.sqlite')

# 判断是否是SQL查询的函数
def is_sql_query(query):
    # 定义一个包含常见 SQL 关键字的列表
    sql_keywords = [
        'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER',
        'TRUNCATE', 'MERGE', 'CALL', 'EXPLAIN', 'DESCRIBE', 'SHOW'
    ]

    # 去掉查询字符串两端的空白字符并转换为大写
    query_upper = query.strip().upper()

    # 遍历 SQL 关键字列表
    for keyword in sql_keywords:
        # 如果查询字符串以某个 SQL 关键字开头，返回 True
        if query_upper.startswith(keyword):
            return True

    # 定义一个正则表达式模式，用于匹配以 SQL 关键字开头的字符串
    sql_pattern = re.compile(
        r'^\s*(SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER|TRUNCATE|MERGE|CALL|EXPLAIN|DESCRIBE|SHOW)\s+',
        re.IGNORECASE  # 忽略大小写
    )

    # 如果正则表达式匹配查询字符串，返回 True
    if sql_pattern.match(query):
        return True

    # 如果查询字符串不符合任何 SQL 关键字模式，返回 False
    return False


# 创建一个表单用于搜索
with st.form("search_form"):
    # 输入框用于输入查询
    query = st.text_input("通过类别、品牌或发布商搜索offer。")
    # 提交按钮
    submitted = st.form_submit_button("搜索")
    # 实例化RetrievalLLM类
    retrieval_llm = RetrievalLLM(
        data_path=DATA_PATH,
        tables=TABLES,
        db_name=DB_NAME,
        openai_api_key=os.getenv('OPENAI_API_KEY'),
    )
    # 如果表单提交
    if submitted:
        # 如果输入内容是SQL语句，则显示SQL执行结果
        if is_sql_query(query):
            st.write(pd.read_sql_query(query, conn))
        # 否则使用LLM从数据库中检索offer
        else:
            # 使用RetrievalLLM实例检索offer
            retrieved_offers = retrieval_llm.retrieve_offers(
                PROMPT_TEMPLATE.format(query)
            )
            # 如果没有找到相关offer
            if not retrieved_offers:
                st.text("未找到相关offer。")
            else:
                # 显示检索到的offer
                st.table(retrieval_llm.parse_output(retrieved_offers, query))
