import requests
import json
from utils import getUrl
url = getUrl("/post_demo/invoke")

content = "学猫叫"
input = {'input':'xxx','name':'zzz'}

response = requests.post(
    url,
    json={'input':json.dumps(input)}
)

print(response.json())

#{'output': {'response': '收到POST请求，处理内容：xxx', 'status': 'success', 'input': 'xxx', 'name': 'zzz', 'demo': None}, 'metadata': {'run_id': '5d2153be-de27-a0d6444d83f7', 'feedback_tokens': []}}
