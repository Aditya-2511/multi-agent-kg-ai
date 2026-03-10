"""agents/weather_agent.py — stub"""
from services.weather_service import get_weather

def weather_agent(state: dict) -> dict:
    result = get_weather(state)
    state.update(result)
    return state