from openai import OpenAI
import streamlit as st
import json
import time
import tiktoken
import os, sys


# 计算消息列表使用的token数量
def num_tokens_from_messages(messages, model):
    """
    Return the number of tokens used by a list of messages.
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        print("Warning: model not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")
    # 定义不同模型的token参数
    if model in {
        "gpt-3.5-turbo-0613",
        "gpt-3.5-turbo-16k-0613",
        "gpt-3.5-turbo-1106"
        "gpt-4-0314",
        "gpt-4-32k-0314",
        "gpt-4-32k-0613",
        "gpt-4-0613",
        "gpt-4-32k-0613",
        "gpt-4",
        "gpt-4o",
        "gpt-3.5-turbo"
    }:
        #定义每条消息的基础 token 数量。这是因为在处理消息时，除了消息的内容本身
        #，还需要考虑消息的元数据（如角色、名称等）和消息格式（如标记、换行符等）。
        # 具体来说，这个值表示每条消息的基础开销，即使消息内容为空，也会有这部分 token 的消耗。
        tokens_per_message = 3
        #定义每条消息中包含名称时的额外 token 数量。
        #这是因为在某些消息格式中，除了消息的内容和角色之外，还可能包含发送者的名称，这会增加额外的 token 开销。
        tokens_per_name = 1
    elif model == "gpt-3.5-turbo-0301":
        tokens_per_message = 4  # 每条消息格式为 <|start|>{role/name}\n{content}<|end|>\n
        tokens_per_name = -1 # 如果有名字，角色会被省略
    else:
        raise NotImplementedError(
            f"""model {model} not supported. Please add it to the num_tokens_from_messages function."""
        )
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3  # 每个回复以 <|start|>assistant<|message|> 开头
    return num_tokens

# 使用缓存，当参数不变时，不会重复创建client
@st.cache_resource
def get_openai_client(url, api_key):
    #使用了缓存，当参数不变时，不会重复创建client
    client = OpenAI(base_url=url, api_key=api_key)
    return client


# 聊天页面
def chat_page():
    st.title("Chat（聊天）")
    # 初始化参数
    api_key = (
        st.session_state.api_key
        if "api_key" in st.session_state and st.session_state.api_key != ""
        else None
    )
    if api_key is None:
        st.error("Please enter your API key in the home.")
        st.stop()

    if "base_url" in st.session_state:
        base_url = st.session_state.base_url
    else:
        base_url = "https://api.openai.com/v1"

    #获取当前脚本文件所在的目录路径
    src_path = os.path.dirname(os.path.realpath(sys.argv[0]))
    #读取默认配置文件
    with open(os.path.join(src_path, 'config/default.json'), 'r', encoding='utf-8') as f:
        config_defalut = json.load(f)

    # 显示配置项
    st.session_state['model_list'] = config_defalut["completions"]["models"]
    model_name = st.selectbox('Models', st.session_state.model_list, key='chat_model_name')

    # 系统提示词选项
    option = st.radio("system_prompt", ("Manual input", "prompts"), horizontal=True, index=0)
    if option == "Manual input":
        system_prompt = st.text_input('System Prompt (Please click the button "clear history" after modification.)',
                                      config_defalut["completions"]["system_prompt"])
    else:
        # 加载预设提示词
        with open(os.path.join(src_path, 'config/prompt.json'), 'r', encoding='utf-8') as f:
            masks = json.load(f)
        masks_zh = [item['name'] for item in masks['zh']]
        masks_zh_name = st.selectbox('prompts', masks_zh)
        for item in masks['zh']:
            if item['name'] == masks_zh_name:
                system_prompt = item['context']
                break
    # 是否使用默认参数
    if not st.checkbox('default param', True):
        max_tokens = st.number_input('Max Tokens', 1, 200000, config_defalut["completions"]["max_tokens"],
                                     key='max_tokens')
        temperature = st.slider('Temperature', 0.0, 1.0, config_defalut["completions"]["temperature"],
                                key='temperature')
        top_p = st.slider('Top P', 0.0, 1.0, config_defalut["completions"]["top_p"], key='top_p')
        stream = st.checkbox('Stream', config_defalut["completions"]["stream"], key='stream')
    else:
        max_tokens = config_defalut["completions"]["max_tokens"]
        temperature = config_defalut["completions"]["temperature"]
        top_p = config_defalut["completions"]["top_p"]
        stream = config_defalut["completions"]["stream"]

    # 初始化聊天记录
    if 'chat_messages' not in st.session_state:
        st.session_state['chat_messages'] = [{"role": "system", "content": system_prompt}]

    # 清除历史记录
    if st.button("clear history"):
        st.session_state.chat_messages = [{"role": "system", "content": system_prompt}]

    # 显示聊天记录
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg['role']):
            st.markdown(msg['content'])

    # 处理用户输入
    if prompt := st.chat_input():
        # 如果用户在输入框中输入了内容
        try:
            # 尝试获取 OpenAI 客户端
            client = get_openai_client(base_url, api_key)
        except Exception as e:
            # 如果获取客户端失败，显示错误信息并停止程序
            st.error(e)
            st.stop()
        # 显示用户的输入内容
        st.chat_message("user").write(prompt)
        with st.chat_message('assistant'):
            # 显示一个“Thinking...”的加载动画
            with st.spinner('Thinking...'):
                # 记录开始时间
                start_time = time.time()
                try:
                    # 临时保存当前的聊天消息
                    temp_chat_messages = st.session_state.chat_messages
                    # 将用户的输入内容添加到聊天消息中
                    temp_chat_messages.append({"role": "user", "content": prompt})
                    # 调用 OpenAI 接口生成回复
                    response = client.chat.completions.create(
                        model=model_name,
                        messages=temp_chat_messages,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        top_p=top_p,
                        stream=stream
                    )
                except Exception as e:
                    # 如果调用接口失败，显示错误信息并停止程序
                    st.error(e)
                    st.stop()
                if response:
                    # 如果设置了流式传输
                    if stream:
                        # 创建一个占位符用于显示流式传输的内容
                        placeholder = st.empty()
                        streaming_text = ''
                        for chunk in response:
                            # 如果流式传输结束，跳出循环
                            if chunk.choices[0].finish_reason == 'stop':
                                break
                            # 获取当前块的内容
                            chunk_text = chunk.choices[0].delta.content
                            if chunk_text:
                                # 累加当前块的内容并更新显示
                                streaming_text += chunk_text
                                placeholder.markdown(streaming_text)
                        # 将流式传输的内容保存为最终消息
                        model_msg = streaming_text
                    else:
                        # 如果没有设置流式传输，直接获取回复内容
                        model_msg = response.choices[0].message.content
                        # 显示回复内容
                        st.markdown(model_msg)
                    # 记录结束时间
                    end_time = time.time()
                    # 将助手的回复添加到聊天消息中
                    temp_chat_messages.append({"role": "assistant", "content": model_msg})
                    # 更新会话状态中的聊天消息
                    st.session_state.chat_messages = temp_chat_messages

                    # 计算当前对话的消耗的token数
                    if config_defalut["completions"]["num_tokens"]:
                        try:
                            # 调用函数计算 token 数量
                            num_tokens = num_tokens_from_messages(st.session_state.chat_messages, model=model_name)
                            # 显示 token 数量信息
                            info_num_tokens = f"use tokens: {num_tokens}"
                            st.info(info_num_tokens)
                        except Exception as e:
                            print(e)
                    # 生成当前对话耗时信息
                    if config_defalut["completions"]["use_time"]:
                        st.info(f"Use time: {round(end_time - start_time, 2)}s")


if __name__ == "__main__":
    chat_page()
