import streamlit as st
from audio_recorder_streamlit import audio_recorder
from openai import OpenAI
from io import BytesIO
import os, sys, json

filter_text = {
    "en": [
        "hate speech",
        "violence",
        "terrorism",
        "child abuse",
        "self-harm",
        "suicide",
        "discrimination",
        "illegal activities",
        "explicit content",
        "harassment"
    ],
    "zh": [
        "仇恨言论",
        "暴力",
        "恐怖主义",
        "虐待儿童",
        "自残",
        "自杀",
        "歧视",
        "非法活动",
        "露骨内容",
        "骚扰"
    ]
}


# 如果text在filter_text中有相同的句子
def filter(text, language):
    if language in filter_text:
        for filter_text_item in filter_text[language]:
            if filter_text_item in text:
                return True
    return False


MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB

st.set_page_config(
    page_title="speech to text",
    layout="wide",
)


@st.cache_resource
def get_openai_client(url, api_key):
    client = OpenAI(base_url=url, api_key=api_key)
    return client


# 定义语音转文字页面
def stt_page():
    st.title("speech to text（语音转文字）")
    st.caption("based on our state-of-the-art open source large-v2 Whisper model")
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

    if "button_active" not in st.session_state:
        st.session_state.button_active = False
    # 获取当前脚本文件的绝对路径，并提取其目录路径。
    src_path = os.path.dirname(os.path.realpath(sys.argv[0]))
    # 打开位于当前脚本目录下的 config/default.json 文件，并以读取模式打开，编码为 UTF-8。
    with open(os.path.join(src_path, 'config/default.json'), 'r', encoding='utf-8') as f:
        # 将打开的 JSON 文件内容加载到 config_defalut 变量中。
        config_defalut = json.load(f)
        # 从配置文件中提取语言列表并存储在 language_list 变量中。
    language_list = config_defalut["stt"]["language"]

    client = get_openai_client(base_url, api_key)
    audio_file = None

    # 选择输入方式：录音或上传
    option = st.radio("Input methods:", ("Recording", "uploading"), horizontal=True, index=1)
    if option == "Recording":
        # 调用 audio_recorder 函数进行录音。
        audio_bytes = audio_recorder()
        # 如果录音成功
        if audio_bytes:
            # 显示文本“Recorded audio”。
            st.text("Recorded audio")
            # 播放录制的音频
            st.audio(audio_bytes, format="audio/wav")
            # 将录制的音频字节数据转换为 BytesIO 对象。
            audio_file = BytesIO(audio_bytes)
            # 设置音频文件的名称为 audio.wav。
            audio_file.name = "audio.wav"
    # 如果用户选择上传方式
    else:
        # 显示提示信息，告知用户当前 OpenAI 接口仅支持最大 25MB 的文件。
        st.write("Attention! Currently, the OpenAI interface only supports up to 25MB.")
        # 创建文件上传控件，允许用户上传音频文件。
        audio_file = st.file_uploader("Upload audio file", type=["wav", "mp3", "webm", "mpeg", "mpga"])
        # 如果用户上传了文件
        if audio_file:
            # 检查文件大小是否超过最大限制（25MB）
            if audio_file.size > MAX_FILE_SIZE:
                # 如果文件过大，显示错误信息。
                st.error("The uploaded file is too large. Please upload an audio smaller than 25MB.")
    # 创建一个下拉选择框，允许用户选择语言。
    language = st.selectbox('language(To add other languages through a configuration file.)', language_list,
                            key='language')

    # 定义一个函数 whisper_online，用于在线调用 Whisper 模型进行语音转文字。
    def whisper_online(audio_file, language):
        # 使用 OpenAI 客户端调用 Whisper 模型，将音频文件转换为文本。
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="text",
            language=language
        )
        # 返回转录文本
        return transcript

    # 创建一个按钮，用户点击后开始语音转文字。
    if st.button("transcribe"):
        # 如果有音频文件：
        if audio_file:
            # 显示等待提示信息
            with st.spinner('please wait...'):
                try:
                    # 调用 whisper_online 函数，进行语音转文字
                    transcript = whisper_online(audio_file, language)
                    # 如果转录文本不过滤
                    if filter(transcript, "zh") == False:
                        # 显示转录结果
                        st.write(transcript)
                        # 否则显示“null”
                    else:
                        st.write("文本中存在敏感内容")
                # 如果发生异常，显示错误信息，停止执行
                except Exception as e:
                    st.error(e)
                    st.stop()
        # 如果没有音频文件，显示警告信息，提示用户先上传音频文件
        else:
            st.warning("Please upload the audio file first.")


if __name__ == "__main__":
    stt_page()
