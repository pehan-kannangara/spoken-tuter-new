from typing import TypedDict


class ClassifierState(TypedDict):
    user_id: str
    role: str
    event_type: str
    payload: dict
    resolved_intent: str
    routed_agent: str
    confidence: float
