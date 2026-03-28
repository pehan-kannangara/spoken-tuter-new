from typing import TypedDict


class ContextState(TypedDict):
    user_id: str
    role: str
    resolved_intent: str
    routed_agent: str
    context: dict
