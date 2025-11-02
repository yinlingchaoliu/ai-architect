# multi_agent_system/plugins/__init__.py
from .weather_agent import WeatherAgent
from .transport_agent import TransportAgent
from .budget_agent import BudgetAgent

__all__ = ["WeatherAgent", "TransportAgent", "BudgetAgent"]