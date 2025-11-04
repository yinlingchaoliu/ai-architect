# tools/rag_system.py
import os
from typing import List

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

class RAGSystem:
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.embeddings = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))
        self.vectorstore = Chroma(
            persist_directory=persist_directory,
            embedding_function=self.embeddings
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )

    async def search(self, query: str, k: int = 3) -> str:
        """在知识库中搜索相关信息"""
        try:
            docs = self.vectorstore.similarity_search(query, k=k)
            results = [doc.page_content for doc in docs]
            return "\n\n".join(results)
        except Exception as e:
            return f"知识库搜索错误: {str(e)}"

    def add_documents(self, documents: List[str]):
        """向知识库添加文档"""
        texts = self.text_splitter.split_text("\n\n".join(documents))
        self.vectorstore.add_texts(texts)