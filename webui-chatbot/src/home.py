import streamlit as st
import json
from utils.env import setDefaultEnv

def import_config_file(file):
    '''
    侧边栏配置导入
    '''
    if file is not None:
        content = file.read()
        try:
            # 解析JSON数据
            json_data = json.loads(content)
            st.success("load config success")
        except Exception as e:
            st.error("load config error:{}".format(e))
        st.session_state.base_url = json_data.get("base_url")
        st.session_state.api_key = json_data.get("api_key")

def home():
    st.title("🏠openai playground")
    st.caption("Please fill in the parameters in the sidebar before using, or import the parameters by uploading a file.")

    setDefaultEnv()

    #通过上传配置的方式导入base_url和api_key
    uploaded_file = st.sidebar.file_uploader("uploaded config", type="json")
    print(uploaded_file)
    if uploaded_file is not None:
        import_config_file(uploaded_file)

    ## 输入方式
    st.session_state.base_url = st.sidebar.text_input('Base URL', st.session_state.base_url)
    st.session_state.api_key =  st.sidebar.text_input('API Key',st.session_state.api_key, type='password')

    option = st.radio("change language:", ("En", "Zh"),horizontal=True,index=1)
    if option == "Zh":
        st.markdown(
                """
                **体验OpenAI多模态功能**
                ## 使用说明
                * 请在侧边栏填写`API Key`，如果没有请在[OpenAI官网](https://platform.openai.com/account/api-keys)获取，如果需要使用代理，请修改`base_url`\n
                * 也可以通过导入json文件自动填充，格式如下：\n
                    ```json
                    {
                        "base_url" : "https://xxx",
                        "api_key" : "sk-xxxx" 
                    }
                    ```
                * 接下来在侧边栏选择需要使用的页面。
                ---------------------------------------------------------
                ### 1 💬chat page  \n
                该页面用于文本对话，选择模型，输入问题，得到回答。[文本生成](/chat)\n

                ### 2 🎞️vision page \n
                该页面用于图像理解，使用gpt-4-vision-preview模型，输入图片和问题，得到回答。[视觉理解](/vision)\n
                
                ### 3 🖼️drawing page \n
                该页面用于图像生成，使用DALL·E模型，输入提示词，输出图片。[文生图](/drawing)\n
                
                ### 4 🗣️speech to text\n
                该页面用于语音转文本，使用whisper模型。[语音转文字](/speech_to_text)\n
                
                ### 5 📢text to speech\n
                该页面用于文本转语音，使用tts模型。[文字转语言](/text_to_speech)\n                                
                """
        )
    elif option == "En":
        st.markdown(
            """
            **Here you can experience all the capabilities provided by OpenAI.**
            ## Instructions for use
            * Please fill in the `API Key` in the sidebar. If you don't have one, you can obtain it from the [OpenAI website](https://platform.openai.com/account/api-keys). If you need to use a proxy, please modify the `base_url`.
            * You can also automatically populate the fields by importing a JSON file with the following format:
            ```json
            {
                "base_url" : "https://xxx",
                "api_key" : "sk-xxxx" 
            }
            ```
            * Next, select the desired page from the sidebar.
            ---------------------------------------------------------
            ### 1 💬chat page
            This page is used for text-based conversations. Select a model, input a question, and get a response. [text-generation](/chat)

            ### 2 🎞️vision page
            This page is used for image understanding. It utilizes the gpt-4-vision-preview model. Input an image and a question, and get a response. [vision](/vision)

            ### 3 🖼️drawing page
            This page is used for image generation. It utilizes the DALL·E model. Input prompts and generate images.  [image-generation](/drawing)

            ### 4 🗣️speech to text
            This page is used for speech-to-text conversion. It utilizes the whisper model. [speech-to-text](/speech_to_text)

            ### 5 📢text to speech
            This page is used for text-to-speech conversion. It utilizes the tts model. [text-to-speech](/text_to_speech)
            """
        )

if __name__ == "__main__":
    home()