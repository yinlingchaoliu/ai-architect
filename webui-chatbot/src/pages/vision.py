from openai import OpenAI
import streamlit as st
import json
import os, sys
import base64
import requests
from utils.env import setDefaultEnv,getBaseUrl,getApiKey

@st.cache_resource
def get_openai_client(url, api_key):
    # 使用了缓存，当参数不变时，不会重复创建client
    client = OpenAI(base_url=url, api_key=api_key)
    return client


def vision_page():
    st.title("GPT-4 with Vision（理解图片内容）")
    st.caption("use GPT-4 to understand images")

    # 初始化参数
    setDefaultEnv()
    base_url = getBaseUrl()
    api_key = getApiKey()

    if api_key is None:
        st.error("Please enter your API key in the home.")
        st.stop()

    # 获取当前脚本的目录路径
    src_path = os.path.dirname(os.path.realpath(sys.argv[0]))
    # 读取默认配置文件
    with open(os.path.join(src_path, 'config/default.json'), 'r', encoding='utf-8') as f:
        config_defalut = json.load(f)
    # 文件上传控件，支持png, jpg, jpeg格式
    upload_images = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg"], label_visibility="collapsed")
    # 最大文件大小设置为5MB
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

    bytes_data = None
    if upload_images is not None:
        # 如果上传的文件超过5MB，显示错误信息
        if upload_images.size > MAX_FILE_SIZE:
            st.error("The uploaded file is too large. Please upload an image smaller than 5MB.")
        else:
            # 获取上传文件的二进制数据
            bytes_data = upload_images.getvalue()
            # 显示上传的图片
            st.image(bytes_data, caption=upload_images.name, width=200)
    # 获取用户输入的文本
    if prompt := st.chat_input():
        # 显示用户输入的文本
        st.chat_message("user").write(prompt)
        with st.chat_message('assistant'):
            with st.spinner('Thinking...'):
                try:
                    # 将图片数据转换为base64编码
                    base64_image = base64.b64encode(bytes_data).decode("utf-8")
                    # 设置请求头
                    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
                    # 设置请求体
                    payload = {
                        "model": "gpt-4-vision-preview",
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": prompt,
                                    },
                                    {
                                        "type": "image_url",
                                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                                    },
                                ],
                            },
                        ],
                        "max_tokens": 300,
                    }
                    # 确保base_url没有尾部的斜杠
                    if base_url.endswith('/'):
                        base_url = base_url[:-1]
                    response = requests.post(
                        base_url + "/chat/completions", headers=headers, json=payload
                    )
                    # 检查状态码是否正常，不正常会触发异常
                    response.raise_for_status()
                    print(response.json())
                    # 获取并显示响应结果
                    result = response.json()["choices"][0]["message"]["content"]
                    st.markdown(result)
                except Exception as e:
                    # 显示异常信息
                    st.error(e)
                    st.stop()


if __name__ == "__main__":
    vision_page()