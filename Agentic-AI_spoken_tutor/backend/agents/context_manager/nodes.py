from backend.agents.context_manager.state import ContextState


# In production this should read/write Redis + PostgreSQL.
SESSION_STORE: dict[str, dict] = {}


def load_context(state: ContextState) -> ContextState:
    existing = SESSION_STORE.get(state["user_id"], {})
    merged = {**existing, "last_intent": state["resolved_intent"], "role": state["role"]}
    return {**state, "context": merged}


def save_context(state: ContextState) -> ContextState:
    SESSION_STORE[state["user_id"]] = state["context"]
    return state
