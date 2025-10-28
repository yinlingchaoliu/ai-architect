# from langchain.schema.runnable import RunnableMap
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableMap
from langserve import RemoteRunnable

openai = RemoteRunnable("http://localhost:8001/openai/")
prompt = ChatPromptTemplate.from_messages(
    [("system", "你是一个喜欢写故事的助手"), ("user", "写一个故事，主题是： {topic}")]
)
# 可以定义自定义链
chain = prompt | RunnableMap({
    "openai": openai
})
response = chain.batch([{"topic": "猫"}])
print(response)
#[{'openai': AIMessage(content='从前，有一个叫做肖恩的男孩，他在一个宁静的乡村里生活。一天，他在家的后院发现了一个小小的，萌萌的猫咪。这只猫咪有一双大大的蓝色眼睛，毛色如同朝霞般的粉色，看起来非常可爱。\n\n肖恩把这只猫咪带回了家，他给她取名为“樱花”，因为她的毛色让他联想到春天盛开的樱花。肖恩非常喜欢樱花，他用心照顾她，每天都会为她准备新鲜的食物和清水，还会陪她玩耍，带她去散步。\n\n樱花也非常喜欢肖恩，她会在肖恩读书的时候躺在他的脚边，会在他伤心的时候安慰他，每当肖恩回家的时候，她总是第一个跑出来迎接他。可是，樱花有一个秘密，她其实是一只会说人话的猫。\n\n这个秘密是在一个月圆的夜晚被肖恩发现的。那天晚上，肖恩做了一个噩梦，他从梦中惊醒，发现樱花正坐在他的床边，用人的语言安慰他。肖恩一开始以为自己在做梦，但是当他清醒过来，樱花还在继续讲话，他才知道这是真的。\n\n樱花向肖恩解释，她是一只来自神秘的猫咪国度的使者，她的任务是保护和帮助那些善良和爱护动物的人。肖恩因为对她的善良和照顾，使她决定向他展现真实的自我。\n\n肖恩虽然感到惊讶，但他并没有因此而害怕或者排斥樱花。他觉得这只使得他更加喜欢樱花，觉得这是他们之间的特殊纽带。\n\n从那天开始，肖恩和樱花的关系变得更加亲密，他们像最好的朋友一样，分享彼此的秘密，一起度过快乐的时光。樱花也用她的智慧和力量，帮助肖恩解决了许多困扰他的问题。\n\n许多年过去了，肖恩长大了，他离开了乡村，去了城市上大学。但是，无论他走到哪里，都会带着樱花。他们的友情和互相的陪伴，让他们无论在哪里，都能感到家的温暖。\n\n最后，肖恩成为了一名作家，他写下了自己和樱花的故事，这个故事被人们广为传播，让更多的人知道了这个关于善良、友情和勇气的故事。而樱花，也永远陪伴在肖恩的身边，成为他生活中不可或缺的一部分。\n\n这就是肖恩和樱花的故事，一个关于男孩和他的猫的故事，充满了奇迹、温暖和爱。', response_metadata={'token_usage': {'completion_tokens': 1050, 'prompt_tokens': 33, 'total_tokens': 1083}, 'model_name': 'gpt-4-0613', 'system_fingerprint': None, 'finish_reason': 'stop', 'logprobs': None}, id='run-c44f1624-ea75-424b-ba3d-e741baf44bda-0', usage_metadata={'input_tokens': 33, 'output_tokens': 1050, 'total_tokens': 1083})}]
