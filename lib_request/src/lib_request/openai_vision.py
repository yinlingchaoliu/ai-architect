
import requests
import json
import os
from dotenv import load_dotenv, find_dotenv
import base64
from openai import OpenAI

from .utils import log

load_dotenv(find_dotenv())

"""
访问视觉模型
"""
class OpenAIVisionClient:

    def __init__(self,model="gpt-4o"):
        self.openai_base_url = os.getenv('OPENAI_BASE_URL')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.debug = False
        self.model = model
        self.client = OpenAI()

    def enableDebug(self,isDebug):
        self.debug = isDebug

    # 图片base64
    def encode_image(self,image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def vision_image_path(self,input,image_path):
        if self.debug:
            log(self.openai_api_key)
            log(self.openai_base_url)

        # Getting the base64 string
        base64_image = self.encode_image(image_path)

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": input},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            },
                        },
                    ],
                }
            ],
            max_tokens=300,
        )

        content = response.choices[0]
        if self.debug:
            log(content)
        return content

    def vision_image_url(self,input,image_url):
        if self.debug:
            log(self.openai_api_key)
            log(self.openai_base_url)

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": input},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url,
                                # "url": f"data:image/jpeg;base64,{base64_image}"
                            },
                        },
                    ],
                }
            ],
            max_tokens=300,
        )
        content = response.choices[0]

        if self.debug:
            log(content)

        return content