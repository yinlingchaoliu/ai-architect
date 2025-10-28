
from dotenv import load_dotenv, find_dotenv
import os
load_dotenv(find_dotenv())

def getUrl(path):
    base_url = os.getenv('SERVER_BASE_URL')
    port = os.getenv('SERVER_PORT')
    url = base_url + ":" + port + path
    print(url)
    return url