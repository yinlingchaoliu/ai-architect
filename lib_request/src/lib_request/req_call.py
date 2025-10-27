
import requests
import json
import os
from dotenv import load_dotenv, find_dotenv

from .utils import log

load_dotenv(find_dotenv())

class OpenAIAssistantClient:

    def __init__(self):
        self.openai_base_url = os.getenv('OPENAI_BASE_URL')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.debug = False

    def enableDebug(self,isDebug):
        self.debug = isDebug

    def request(self,content):
        if self.debug:
            log(self.openai_api_key)
            log(self.openai_base_url)

        url = self.openai_base_url + "/chat/completions"

        payload = json.dumps({
            "model": "gpt-4",
            "messages": [
                {"role": "system", "content": "assistant"},
                {"role": "user", "content": content}
            ]
        })
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + self.openai_api_key,
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        if self.debug:
            log(response.text)

        return response.text