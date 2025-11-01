from llama_index.llms.huggingface import HuggingFaceLLM
from llama_index.core.llms import ChatMessage

llm = HuggingFaceLLM(
    model_name="/root/app/llm/Qwen/Qwen2___5-0___5B-Instruct",
    tokenizer_name="/root/app/llm/Qwen/Qwen2___5-0___5B-Instruct",
    model_kwargs={"trust_remote_code":True},
    tokenizer_kwargs={"trust_remote_code":True}
)

rsp = llm.chat(messages=[ChatMessage(content="xtuner是什么？")])
print(rsp)
print(llm)