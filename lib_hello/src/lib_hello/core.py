class HelloClient:
    """Hello SDK 的主客户端类"""

    def __init__(self, name: str = "World", language: str = "en"):
        self.name = name
        self.language = language
        self._greetings = {
            "en": "Hello",
            "es": "Hola",
            "fr": "Bonjour",
            "zh": "你好"
        }

    def greet(self, message: str = None) -> str:
        """生成问候语"""
        greeting = self._greetings.get(self.language, self._greetings["en"])

        if message:
            return f"{greeting}, {self.name}! {message}"
        else:
            return f"{greeting}, {self.name}!"

    def set_language(self, language: str) -> None:
        """设置问候语言"""
        if language in self._greetings:
            self.language = language
        else:
            raise ValueError(f"Unsupported language: {language}")

    def get_supported_languages(self) -> list:
        """获取支持的语言列表"""
        return list(self._greetings.keys())


def say_hello(name: str = "World", language: str = "en") -> str:
    """快速问候函数"""
    client = HelloClient(name, language)
    return client.greet()