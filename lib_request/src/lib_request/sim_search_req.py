from typing import List

from lib_request import ReqEmbeddingClient
from lib_request.sim_search import SimilaritySearchBase

"""
文本相似度查询 with req
"""
class SimSearchReq(SimilaritySearchBase):

    def __init__(self):
        super().__init__()
        self.client = ReqEmbeddingClient()

    def get_embedding(self,text:str) -> List[float]:
        self.client.enableDebug(self.debug)
        return self.client.get_embedding(text)