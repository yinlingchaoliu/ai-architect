
import logging
# 配置日志
logging.basicConfig(level=getattr(logging, "INFO"))
logger = logging.getLogger("openai_request")

def log(msg):
    logger.info(msg)