import sqlite3
import numpy as np
import pandas as pd
from langchain_openai import OpenAIEmbeddings
from langchain_openai import OpenAI
from langchain_community.utilities import SQLDatabase
from langchain_experimental.sql import SQLDatabaseChain


class RetrievalLLM:
    """一个类，用于使用大型语言模型（LLM）检索和重新排序offer。

    参数:
        data_path (str): 包含数据CSV文件的目录路径。
        tables (list[str]): 数据CSV文件的名称列表。
        db_name (str): 用于存储数据的SQLite数据库名称。
        openai_api_key (str): OpenAI API密钥。

    属性:
        data_path (str): 包含数据CSV文件的目录路径。
        tables (list[str]): 数据CSV文件的名称列表。
        db_name (str): 用于存储数据的SQLite数据库名称。
        openai_api_key (str): OpenAI API密钥。
        db (SQLDatabase): SQLite数据库连接。
        llm (OpenAI): OpenAI LLM客户端。
        embeddings (OpenAIEmbeddings): OpenAI嵌入客户端。
        db_chain (SQLDatabaseChain): 与LLM集成的SQL数据库链。
    """

    def __init__(self, data_path, tables, db_name, openai_api_key):
        # 初始化类属性
        self.data_path = data_path
        self.tables = tables
        self.db_name = db_name
        self.openai_api_key = openai_api_key

        # 读取CSV文件并存储到数据帧字典中
        dfs = {}
        for table in self.tables:
            dfs[table] = pd.read_csv(f"{self.data_path}/{table}.csv")

        # 将数据帧写入SQLite数据库
        with sqlite3.connect(self.db_name) as local_db:
            for table, df in dfs.items():
                df.to_sql(table, local_db, if_exists="replace")

        # 创建SQL数据库连接
        self.db = SQLDatabase.from_uri(f"sqlite:///{self.db_name}")
        # 创建OpenAI LLM客户端
        self.llm = OpenAI(
            temperature=0, verbose=True, openai_api_key=self.openai_api_key
        )
        # 创建OpenAI嵌入客户端
        self.embeddings = OpenAIEmbeddings(openai_api_key=self.openai_api_key)
        # 创建SQL数据库链
        self.db_chain = SQLDatabaseChain.from_llm(self.llm, self.db)

    def retrieve_offers(self, prompt):
        """使用LLM从数据库中检索offer。

        参数:
            prompt (str): 用于检索offer的提示。

        返回:
            list[str]: 检索到的offer列表。
        """

        # 运行SQL数据库链以检索offer
        retrieved_offers = self.db_chain.run(prompt)
        # 如果retrieved_offers是"None"，则返回None，否则返回检索到的offer
        return None if retrieved_offers == "None" else retrieved_offers

    def get_embeddings(self, documents):
        """使用LLM获取文档的嵌入。

        参数:
            documents (list[str]): 文档列表。

        返回:
            np.ndarray: 包含文档嵌入的NumPy数组。
        """

        # 如果文档列表只有一个文档，将单个文档的嵌入转换为Numpy数组
        if len(documents) == 1:
            return np.asarray(self.embeddings.embed_query(documents[0]))
        else:
            # 否则获取每个文档的嵌入并存储到列表中
            embeddings_list = []
            for document in documents:
                embeddings_list.append(self.embeddings.embed_query(document))
            return np.asarray(embeddings_list)

    def parse_output(self, retrieved_offers, query):
        """解析retrieve_offers()方法的输出并返回一个数据帧。

        参数:
            retrieved_offers (list[str]): 检索到的offer列表。
            query (str): 用于检索offer的查询。

        返回:
            pd.DataFrame: 包含匹配相似度和offer的数据帧。
        """

        # 分割检索到的offer
        top_offers = retrieved_offers.split("#")

        # 获取查询的嵌入
        query_embedding = self.get_embeddings([query])
        # 获取offer的嵌入
        offer_embeddings = self.get_embeddings(top_offers)

        # offer_embeddings是一个二维的Numpy数组，包含多个offer的嵌入向量。
        # query_embedding是一个二维的Numpy数组，包含查询的嵌入向量。
        # query_embedding.T是查询嵌入的转置，使其成为一个列向量，便于进行矩阵乘法。
        # np.dot()计算每个offer嵌入向量与查询嵌入向量之间的点积（内积），结果是一个二维数组，其中每个元素表示一个offer与查询之间的相似度分数。
        # .flatten() 将二维数组转换为一维数组，得到每个 offer 与查询之间的相似度分数列表。
        sim_scores = np.dot(offer_embeddings, query_embedding.T).flatten()
        # 计算相似度得分，转换为百分比形式
        sim_scores = [p * 100 for p in sim_scores]

        # 创建数据帧并按相似度排序
        df = (
            pd.DataFrame({"匹配相似度 %": sim_scores, "offer": top_offers})
            .sort_values(by=["匹配相似度 %"], ascending=False)
            .reset_index(drop=True)
        )
        df.index += 1
        return df
