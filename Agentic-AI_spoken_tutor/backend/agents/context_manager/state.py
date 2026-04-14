from typing import TypedDict


class ContextState(TypedDict):
    user_id: str
    role: str
    resolved_intent: str
    sub_intent: str
    pathway: str
    routed_agent: str
    routing_targets: list[str]
    policy_flags: dict
    fallback_mode: str
    payload: dict
    context: dict
