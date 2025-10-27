import requests
import json
import os
from dotenv import load_dotenv, find_dotenv

from .utils import log

load_dotenv(find_dotenv())

"""
先逐步简单封装,了解原理
"""
class DeepSeekModelListClient:

    def __init__(self):
        self.openai_base_url = os.getenv('DEEPSEEK_API_BASE_URL')
        self.openai_api_key = os.getenv('DEEPSEEK_API_KEY')
        self.debug = False

    def enableDebug(self,isDebug):
        self.debug = isDebug

    def model_list(self):
        if self.debug:
            log(self.openai_base_url)
            log(self.openai_api_key)

        url = self.openai_base_url + "/models"

        payload = {}
        headers = {
            'Accept': 'application/json',
            'Authorization': 'Bearer '+self.openai_api_key
        }

        response = requests.request("GET", url, headers=headers, data=payload)

        if self.debug:
            log(response.text)
        return response.text