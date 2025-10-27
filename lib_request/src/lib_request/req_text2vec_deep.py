import requests
import json
import os
from dotenv import load_dotenv, find_dotenv

from .deprecated import deprecated
from .utils import log

load_dotenv(find_dotenv())

"""
先逐步简单封装,了解原理
"""
@deprecated("deepseek不支持embedding")
class DeepSeekEmbeddingClient:

    def __init__(self):
        self.openai_base_url = os.getenv('DEEPSEEK_API_BASE_URL')
        self.openai_api_key = os.getenv('DEEPSEEK_API_KEY')
        self.debug = False

    def enableDebug(self,isDebug):
        self.debug = isDebug

    def get_embedding(self,text):
        if self.debug:
            log(self.openai_base_url)
            log(self.openai_api_key)

        url = self.openai_base_url + "/chat/completions"
        log(url)

        payload = json.dumps({
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "需要转换为向量的文本内容"},
                {"role": "user", "content": text}
            ],
            "stream": False
        })

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + self.openai_api_key,
        }

        response = requests.request("POST", url, headers=headers, data=payload)

        embedding = None
        if response.status_code == 200:
            embedding = response.json().get("embedding")
            if self.debug:
                log(embedding)
        log(response.status_code)
        log(response.json())
        return embedding