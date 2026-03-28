from backend.agents.context_manager.nodes import load_context, save_context
from backend.agents.context_manager.state import ContextState


def run_context_manager(user_id: str, role: str, resolved_intent: str, routed_agent: str) -> ContextState:
    state: ContextState = {
        "user_id": user_id,
        "role": role,
        "resolved_intent": resolved_intent,
        "routed_agent": routed_agent,
        "context": {},
    }
    state = load_context(state)
    state = save_context(state)
    return state
