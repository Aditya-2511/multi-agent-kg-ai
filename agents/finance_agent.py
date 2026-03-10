"""agents/finance_agent.py — stub"""
from services.finance_service import get_finance_data

def finance_agent(state: dict) -> dict:
    result = get_finance_data(state)
    state.update(result)
    return state