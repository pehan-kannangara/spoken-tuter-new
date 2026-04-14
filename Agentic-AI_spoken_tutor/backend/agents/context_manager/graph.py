from backend.agents.context_manager.nodes import load_context, save_context
from backend.agents.context_manager.state import ContextState


def run_context_manager(user_id: str, role: str, classifier_state: dict, payload: dict) -> ContextState:
    state: ContextState = {
        "user_id": user_id,
        "role": role,
        "resolved_intent": classifier_state["resolved_intent"],
        "sub_intent": classifier_state.get("sub_intent", "assessment"),
        "pathway": classifier_state.get("pathway", "ielts"),
        "routed_agent": classifier_state["routed_agent"],
        "routing_targets": classifier_state.get("routing_targets", [classifier_state["routed_agent"]]),
        "policy_flags": classifier_state.get("policy_flags", {}),
        "fallback_mode": classifier_state.get("fallback_mode", "safe_default"),
        "payload": payload,
        "context": {},
    }
    state = load_context(state)
    state = save_context(state)
    return state
