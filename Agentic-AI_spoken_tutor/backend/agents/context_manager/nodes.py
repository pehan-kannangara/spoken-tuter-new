from backend.agents.context_manager.state import ContextState


# In production this should read/write Redis + PostgreSQL.
SESSION_STORE: dict[str, dict] = {}


def _build_context_package(state: ContextState, existing: dict) -> dict:
    payload = state.get("payload", {}) or {}
    history = list(existing.get("history", []))
    history.append(
        {
            "intent": state["resolved_intent"],
            "agent": state["routed_agent"],
            "pathway": state["pathway"],
        }
    )
    history = history[-8:]

    return {
        "actor": {
            "user_id": state["user_id"],
            "role": state["role"],
            "pathway": state["pathway"],
        },
        "workflow": {
            "intent": state["resolved_intent"],
            "sub_intent": state["sub_intent"],
            "routed_agent": state["routed_agent"],
            "routing_targets": state["routing_targets"],
            "event_type": state["resolved_intent"],
        },
        "quality_policy": {
            "strict_rubric": bool(state["policy_flags"].get("strict_rubric", False)),
            "require_human_review": bool(state["policy_flags"].get("require_human_review", False)),
            "minimum_quality_score": 85 if state["policy_flags"].get("strict_rubric") else 70,
        },
        "screening_policy": {
            "business_screening_mode": bool(state["policy_flags"].get("business_screening_mode", False)),
            "preferred_domains": payload.get("preferred_domains", ["business"]),
            "job_level": payload.get("job_level"),
            "role_name": payload.get("role_name"),
        },
        "constraints": {
            "tool_budget": 5,
            "consent": payload.get("consent", "assumed"),
            "fallback_mode": state.get("fallback_mode", "safe_default"),
        },
        "history": history,
        "last_intent": state["resolved_intent"],
    }


def load_context(state: ContextState) -> ContextState:
    existing = SESSION_STORE.get(state["user_id"], {})
    merged = _build_context_package(state, existing)
    return {**state, "context": merged}


def save_context(state: ContextState) -> ContextState:
    SESSION_STORE[state["user_id"]] = state["context"]
    return state
