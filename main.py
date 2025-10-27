#!/usr/bin/env python3
"""
主程序 - 演示如何使用本地 hello SDK
"""

import sys
import os

from lib_request import OpenAIAssistantClient, OpenAIEmbeddingClient, DeepSeekEmbeddingClient, DeepSeekModelListClient, \
    SimSearchReq, SimSearchOpenAI

"""手写request请求"""
def testCall():
    client = OpenAIAssistantClient()
    client.enableDebug(True)
    client.request("hello")

def testOpenAIembedding():
    embedding = OpenAIEmbeddingClient()
    embedding.enableDebug(True)
    embedding.get_embedding("你好")

def testDeepSeekEmbedding():
    embedding = DeepSeekEmbeddingClient()
    embedding.enableDebug(True)
    embedding.get_embedding("你好")

def testDeepSeekModelList():
    model = DeepSeekModelListClient()
    model.enableDebug(True)
    model.model_list()

def search_req():
    documents = [
        "OpenAI的ChatGPT是一个强大的语言模型。",
        "天空是蓝色的,阳光灿烂。",
        "人工智能正在改变世界。",
        "Python是一种流行的编程语言。"
    ]

    query = "天空是什么颜色的？"

    search = SimSearchReq()
    search.enableDebug(True)
    most_similar_document, similarity_score = search.search_documents(query, documents)
    print(f"最相似的文档: {most_similar_document}")
    print(f"相似性得分: {similarity_score}")


def search_openai():
    documents = [
        "OpenAI的ChatGPT是一个强大的语言模型。",
        "天空是蓝色的,阳光灿烂。",
        "人工智能正在改变世界。",
        "Python是一种流行的编程语言。"
    ]

    query = "天空是什么颜色的？"

    search = SimSearchOpenAI()
    search.enableDebug(True)
    most_similar_document, similarity_score = search.search_documents(query, documents)
    print(f"最相似的文档: {most_similar_document}")
    print(f"相似性得分: {similarity_score}")


if __name__ == "__main__":
    search_openai()
