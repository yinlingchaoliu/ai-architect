from dataclasses import dataclass

@dataclass
class ReqBean:
    input: str = ""
    name: str = None

@dataclass
class RespBean:
    response: str = ""
    status: str = ""
    input: str = ""
    name: str = None
    demo:str = None
