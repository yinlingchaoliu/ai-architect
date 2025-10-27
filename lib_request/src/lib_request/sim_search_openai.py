from typing import List

from lib_request import OpenAIEmbeddingClient
from lib_request.sim_search import SimilaritySearchBase

"""
文本相似度查询 with req
"""
class SimSearchOpenAI(SimilaritySearchBase):

    def __init__(self):
        super().__init__()
        self.client = OpenAIEmbeddingClient()

    def get_embedding(self,text:str) -> List[float]:
        self.client.enableDebug(self.debug)
        return self.client.get_embedding(text)