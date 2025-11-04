# utils/logger.py
from colorama import Fore, Style
import logging


class ColorLogger:
    COLORS = {
        'analyzer': Fore.BLUE,
        'moderator': Fore.MAGENTA,
        'technical_expert': Fore.GREEN,
        'business_expert': Fore.YELLOW,
        'research_expert': Fore.CYAN
    }

    @classmethod
    def log_agent_speech(cls, agent_name: str, content: str):
        color = cls.COLORS.get(agent_name, Fore.WHITE)
        print(f"\n{color}[{agent_name}]{Style.RESET_ALL}: {content}")