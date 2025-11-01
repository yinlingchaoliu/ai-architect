from llama_index.core import VectorStoreIndex,SimpleDirectoryReader,Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.huggingface import HuggingFaceLLM

#初始化一个HuggingFaceEmbedding对象，用于将文本转换为向量表示
embed_model = HuggingFaceEmbedding(
#指定了一个预训练的sentence-transformer模型的路径
    model_name="/root/app/llm/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2/Ceceliachenen/paraphrase-multilingual-MiniLM-L12-v2"
)

#将创建的嵌入模型赋值给全局设置的embed_model属性，
#这样在后续的索引构建过程中就会使用这个模型。
Settings.embed_model = embed_model
llm = HuggingFaceLLM(
    model_name="/root/app/llm/Shanghai_AI_Laboratory/internlm2-chat-1_8b",
    tokenizer_name="/root/app/llm/Shanghai_AI_Laboratory/internlm2-chat-1_8b",
    model_kwargs={"trust_remote_code":True},
    tokenizer_kwargs={"trust_remote_code":True}
)
#设置全局的llm属性，这样在索引查询时会使用这个模型。
Settings.llm = llm
print("llm",llm)
#从指定目录读取所有文档，并加载数据到内存中
documents = SimpleDirectoryReader("/root/app/project/llamindex_demo/data").load_data()
print("documents",documents)
#创建一个VectorStoreIndex，并使用之前加载的文档来构建索引。
# 此索引将文档转换为向量，并存储这些向量以便于快速检索。
index = VectorStoreIndex.from_documents(documents)
# 创建一个查询引擎，这个引擎可以接收查询并返回相关文档的响应。
query_engine = index.as_query_engine()
response = query_engine.query("xtuner是什么?")

print(response)