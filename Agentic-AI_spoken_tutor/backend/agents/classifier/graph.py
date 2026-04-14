from backend.agents.classifier.nodes import classify_intent
from backend.agents.classifier.state import ClassifierState


def run_classifier(user_id: str, role: str, event_type: str, payload: dict) -> ClassifierState:
    initial: ClassifierState = {
        "user_id": user_id,
        "role": role,
        "event_type": event_type,
        "payload": payload,
        "resolved_intent": "",
        "sub_intent": "",
        "pathway": "",
        "routed_agent": "",
        "routing_targets": [],
        "confidence": 0.0,
        "fallback_mode": "safe_default",
        "policy_flags": {},
    }
    return classify_intent(initial)
