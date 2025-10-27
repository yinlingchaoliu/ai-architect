from typing import List

import os

from dotenv import load_dotenv, find_dotenv

from .utils import log
from openai import OpenAI

load_dotenv(find_dotenv())

"""
先逐步简单封装,了解原理
"""
class OpenAIEmbeddingClient:

    def __init__(self,model="text-embedding-ada-002"):
        self.openai_base_url = os.getenv('OPENAI_BASE_URL')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.model = model
        self.client = OpenAI()
        self.debug = False

    def enableDebug(self,isDebug):
        self.debug = isDebug

    def get_embedding(self,text)-> List[float]:
        response = self.client.embeddings.create(
            input=text,
            model=self.model
        )

        embedding = response.data[0].embedding
        if self.debug:
            log(embedding)

        return embedding
