from typing import List

import requests
import json
import os

from dotenv import load_dotenv, find_dotenv
from .utils import log

load_dotenv(find_dotenv())

"""
先逐步简单封装,了解原理
"""
class ReqEmbeddingClient:

    def __init__(self):
        self.openai_base_url = os.getenv('OPENAI_BASE_URL')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.debug = False

    def enableDebug(self,isDebug):
        self.debug = isDebug

    def get_embedding(self,text)-> List[float]:
        if self.debug:
            log(self.openai_api_key)
            log(self.openai_base_url)

        url = self.openai_base_url + "/embeddings"

        payload = json.dumps({
            "model": "text-embedding-ada-002",
            "input": text
        })

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + self.openai_api_key,
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        if self.debug:
            log(response.text)
            log(response.json()['data'][0]['embedding'])

        return response.json()['data'][0]['embedding']