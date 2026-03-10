"""
agents/flight_agent.py  — stub, replace with real flight service
"""
from services.flight_service import get_flights


def flight_agent(state: dict) -> dict:
    result = get_flights(state)
    state.update(result)
    return state