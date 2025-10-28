import requests
import json
from utils import getUrl
url = getUrl("/get_demo/invoke")

input = {'input':'udfdfsj','name':'zzz'}

response = requests.get(
    url,
    params=input
)

print(response.json())
#{'output': {'content': '为什么猫不参加电脑游戏比赛？\n\n因为每次它想按“ESC”键的时候，总是不小心按了“PAWS”键！', 'additional_kwargs': {'refusal': None}, 'responpletion_tokens': 52, 'prompt_tokens': 20, 'total_tokens': 72, 'completion_tokens_details': None, 'prompt_tokens_details': None}, 'model_provider': 'openai', 'model_name': 'gpt-4', 'system_fingerprint': 'fp_5603ee5e2e', 'id': 'chatcmpl-CVXkWKeHHmDoX2FCtrbTme5WVCOo5', 'finish_reason': 'stop', 'logprobs': None}, 'type': 'ai', 'name': None, 'id': 'lc_run--afaaf52d-b936-44b6-ac8a-79546d8b1393-0', 'tool_calls': [], 'invalid_tool_calls': [], 'usage_metadata': {'input_tokens': 20, 'output_tokens': 52, 'total_tokens': 72, 'input_token_details': {}, 'output_token_details': {}}}, 'metadata': {'run_id': '5c9470c1-f8b1-42d9-b891-0c9838e60aee', 'feedback_tokens': []}}
