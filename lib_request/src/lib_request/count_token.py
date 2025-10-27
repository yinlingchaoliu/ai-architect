from openai import OpenAI
# pip install --upgrade tiktoken
#tiktoken 用来统计token使用
import tiktoken

client = OpenAI()
# 初始化 tiktoken 编码器
encoder = tiktoken.encoding_for_model("gpt-4")

def count_tokens(text):
    encoder.encode(text)
    # 将输入的文本text转换为对应的token列表。具体来说，它使用tiktoken库中的编码器将文本进行编码，以便后续处理。
    tokens = encoder.encode(text)
    # 统计文本中的 token 数量
    return len(tokens)