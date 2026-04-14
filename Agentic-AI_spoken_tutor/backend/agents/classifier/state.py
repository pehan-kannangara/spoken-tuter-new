from typing import TypedDict


class ClassifierState(TypedDict):
    user_id: str
    role: str
    event_type: str
    payload: dict
    resolved_intent: str
    sub_intent: str
    pathway: str
    routed_agent: str
    routing_targets: list[str]
    confidence: float
    fallback_mode: str
    policy_flags: dict
