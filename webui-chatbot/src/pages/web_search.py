import time
from datetime import datetime
import requests
import streamlit as st
import wikipedia
from bs4 import BeautifulSoup
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from streamlit_chat import message

import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

global doc_search
from langchain.globals import set_verbose

doc_search = None

# 设置详细模式
set_verbose(True)

# 设置Streamlit的标题
st.markdown("<h1 style='text-align: center; color: Black;'>基于 Web URL 的问答</h1>", unsafe_allow_html=True)

# 创建三个列，用于布局
buff, col, buff2 = st.columns([1, 3, 1])

# 初始化ChatOpenAI对象，指定使用的模型
chat = ChatOpenAI(model_name="gpt-4o")

# 初始化会话状态中的消息列表
if 'all_messages' not in st.session_state:
    st.session_state.all_messages = []


# 初始化FAISS向量数据库的函数
def init_db(wiki_content):
    print("初始化FAISS向量数据库...")
    # 使用CharacterTextSplitter将文本分割成多个块
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
    )
    # 将维基百科内容分割成多个文本块
    texts = text_splitter.split_text(wiki_content)
    # 使用OpenAIEmbeddings生成文本嵌入
    embeddings = OpenAIEmbeddings()
    global doc_search
    # 使用FAISS创建向量数据库
    doc_search = FAISS.from_texts(texts, embeddings)


# 创建一个函数来获取机器人响应
def get_bot_response(user_query):
    # 在向量数据库中进行相似性搜索，返回6个结果
    docs = doc_search.similarity_search(user_query, K=6)
    main_content = user_query + "\n\n"
    # 拼接用户查询和相似的文本内容
    for doc in docs:
        main_content += doc.page_content + "\n\n"
    messages.append(HumanMessage(content=main_content))
    # 调用OpenAI接口获取响应
    ai_response = chat.invoke(messages).content
    # 将刚刚添加的 HumanMessage 从 messages 列表中移除。这样做的原因是，main_content 包含了用户的原始查询和相似文本内容，
    # 但在实际的对话历史中，我们只希望保留用户的原始查询和 AI 的响应，而不是包含相似文本内容的查询。
    messages.pop()
    # 将用户查询添加到消息列表
    messages.append(HumanMessage(content=user_query))
    # 将用户查询添加到消息列表
    messages.append(AIMessage(content=ai_response))
    return ai_response


# 创建一个显示消息的函数
def display_messages(all_messages):
    for msg in all_messages:
        if msg['user'] == 'user':
            message(f"You ({msg['time']}): {msg['text']}", is_user=True, key=int(time.time_ns()))
        else:
            message(f"Wiki-Bot ({msg['time']}): {msg['text']}", key=int(time.time_ns()))


# 创建一个发送消息的函数
def send_message(user_query, all_messages):
    if user_query:
        # 将用户消息添加到消息列表
        all_messages.append({'user': 'user', 'time': datetime.now().strftime("%H:%M"), 'text': user_query})
        # 获取机器人的响应
        bot_response = get_bot_response(user_query)
        # 将机器人的响应添加到消息列表
        all_messages.append({'user': 'bot', 'time': datetime.now().strftime("%H:%M"), 'text': bot_response})
        # 更新会话状态中的消息列表
        st.session_state.all_messages = all_messages


def get_wiki(search):
    # 将语言设置为简体中文
    lang = "zh"

    """
    从维基百科获取摘要
    """
    # 设置维基百科的语言
    wikipedia.set_lang(lang)
    # 获取维基百科摘要
    summary = wikipedia.summary(search, sentences=5)

    """
    抓取所请求查询的维基百科页面
    """

    # 根据用户输入和语言创建URL
    url = f"https://{lang}.wikipedia.org/wiki/{search}"

    # 向URL发送GET请求并解析HTML内容
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")

    # 提取页面的主要内容
    content_div = soup.find(id="mw-content-text")

    # 摘录所有内容段落
    paras = content_div.find_all('p')

    # 将段落连接成整页内容
    full_page_content = ""
    for para in paras:
        full_page_content += para.text

    # 返回整页内容和摘要
    return full_page_content, summary


# 创建一个列表来存储消息
messages = [
    SystemMessage(
        content="你是一个问答机器人，你将回答用户的所有问题。如果你不知道答案，输出“对不起，我不知道”。")
]

# 创建用于用户输入的文本框
search = st.text_input("请输入要检索的关键词")

# 输入的关键词不为空
if len(search):
    # 获取维基百科内容和摘要
    wiki_content, summary = get_wiki(search)
    if len(wiki_content):
        try:
            # 显示摘要
            st.write(summary)
            # 创建用户发送消息的输入文本框
            user_query = st.text_input("You: ", "", key="input")
            # 创建发送按钮
            send_button = st.button("Send")
            if len(user_query) and send_button:
                # 初始化向量数据库
                if doc_search is None:
                    init_db(wiki_content)
            # 如果向量数据库已初始化，则发送消息
            if doc_search is not None:
                send_message(user_query, st.session_state.all_messages)
                display_messages(st.session_state.all_messages)

        except Exception as e:
            # 显示错误信息
            st.write(f"执行报错：{e}")
