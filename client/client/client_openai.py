# from langchain.schema.runnable import RunnableMap
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableMap
from langserve import RemoteRunnable

from client.client.utils import getUrl
url = getUrl("/openai/")

openai = RemoteRunnable(url)
prompt = ChatPromptTemplate.from_messages(
    [("system", "你是一个喜欢写故事的助手"), ("user", "写一个故事，主题是： {topic}")]
)
# 可以定义自定义链
chain = prompt | RunnableMap({
    "openai": openai
})
response = chain.batch([{"topic": "猫"}])
print(response)

#[{'openai': AIMessage(content='在一个宁静的小镇上，住着一只名叫米斯特的灰色短毛猫。米斯特非常喜欢探险，每天他都会离开他温暖的家，去探索周围的环境。\n\n一天，米特的好奇心促使他走进了小巷。\n\n随着他接近那座小屋，他听到了微弱的呢喃声。米斯特小心翼翼地走近，发现呢喃声来自于一只困在小屋里的黑白相间的小猫。它的一只脚似乎被n从那一天起，米斯特和那只名叫奥利的黑白小猫成了不可分割的朋友。他们一起探索小镇，一起分享美味的食物，一起在火炉旁打盹。\n\n米斯特的主人很快就注意到了米斯特的新因为它终于有了一个家和一个欢乐的伴侣。\n\n尽管它们来自不同的地方，米斯特和奥利都知道友情是无价的，而冒险则是他们最喜欢的共同爱好。他们的故事在小镇上传开了，成为 None}, response_metadata={'token_usage': {'completion_tokens': 652, 'prompt_tokens': 39, 'total_tokens': 691, 'completion_tokens_details': None, 'prompt_tokens_details': None}, 'model_provider': 'openai', 'model_name': 'gpt-4', 'system_fingerprint': 'fp_5603ee5e2e', 'id': 'chatcmpl-CVXT0pAgEWm22QOP6neqz72EJNONI', 'finish_reason': 'stop', 'logprobs': None}, id='lc_run--e6f8b686-b5ba-4e08-a936-ef0598a59502-0', usage_metadata={'input_tokens': 39, 'output_tokens': 652, 'total_tokens': 691, 'input_token_details': {}, 'output_token_details': {}})}]