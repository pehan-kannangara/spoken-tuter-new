from backend.agents.classifier.state import ClassifierState


INTENT_TO_AGENT = {
    # ── Assessment / Scoring ─────────────────────────────────────────────
    "start_initial_assessment": "assessment_scoring",
    "submit_assessment_part":   "assessment_scoring",
    "submit_response":          "assessment_scoring",
    "score_session":            "assessment_scoring",
    # ── Feedback / Pathway ───────────────────────────────────────────────
    "view_feedback":            "feedback_pathway",
    "get_feedback":             "feedback_pathway",
    "view_learning_pathway":    "feedback_pathway",
    "get_pathway":              "feedback_pathway",
    "get_progress":             "feedback_pathway",
    # ── Recruiter Screening ──────────────────────────────────────────────
    "create_screening_pack":    "recruiter_screening",
    "add_candidate":            "recruiter_screening",
    "start_candidate_session":  "recruiter_screening",
    "get_pack_results":         "recruiter_screening",
    "get_pack":                 "recruiter_screening",
    "list_packs":               "recruiter_screening",
    "send_candidate_assessment":"recruiter_screening",
    # ── Monitoring / Analytics ───────────────────────────────────────────
    "view_class_analytics":     "monitoring_analytics",
    "class_overview":           "monitoring_analytics",
    "learner_detail":           "monitoring_analytics",
    "risk_check":               "monitoring_analytics",
    "create_class":             "monitoring_analytics",
    "get_classes":              "monitoring_analytics",
    "scheduled_risk_check":     "monitoring_analytics",
    # ── QA Engine ────────────────────────────────────────────────────────
    "generate_item":            "qa_workflow",
    "validate_item":            "qa_workflow",
    "activate_item":            "qa_workflow",
    "monitor_drift":            "qa_workflow",
    "retire_item":              "qa_workflow",
}

KNOWN_PATHWAYS = {"ielts", "cefr", "business_english"}


def _resolve_pathway(state: ClassifierState) -> str:
    payload = state.get("payload", {}) or {}
    candidate = str(payload.get("pathway") or payload.get("screening_pathway") or "").strip().lower()
    if candidate in KNOWN_PATHWAYS:
        return candidate
    role = state.get("role", "")
    if role == "recruiter":
        return "business_english"
    return "ielts"


def _resolve_sub_intent(event_type: str) -> str:
    if event_type.startswith("qa_") or event_type in {
        "generate_item",
        "validate_item",
        "activate_item",
        "monitor_drift",
        "retire_item",
    }:
        return "quality_assurance"
    if "screen" in event_type or "candidate" in event_type:
        return "talent_screening"
    if "feedback" in event_type or "pathway" in event_type:
        return "learning_feedback"
    if "class" in event_type or "analytics" in event_type or "risk" in event_type:
        return "monitoring"
    return "assessment"


def _routing_targets(primary_agent: str, role: str, pathway: str) -> list[str]:
    targets = [primary_agent]
    if pathway == "business_english" and primary_agent != "recruiter_screening":
        targets.append("recruiter_screening")
    if role in {"admin", "system"} and "qa_workflow" not in targets:
        targets.append("qa_workflow")
    return targets


def _policy_flags(role: str, pathway: str, sub_intent: str, confidence: float, known_event: bool) -> dict:
    high_stakes = role == "recruiter" or sub_intent == "talent_screening"
    return {
        "require_human_review": high_stakes and confidence < 0.9,
        "strict_rubric": high_stakes,
        "business_screening_mode": pathway == "business_english",
        "known_event": known_event,
    }


def classify_intent(state: ClassifierState) -> ClassifierState:
    event_type = state["event_type"].strip()
    resolved_intent = event_type
    known_event = event_type in INTENT_TO_AGENT
    routed_agent = INTENT_TO_AGENT.get(event_type, "assessment_scoring")

    pathway = _resolve_pathway(state)
    sub_intent = _resolve_sub_intent(event_type)

    if state["role"] == "recruiter" and routed_agent == "assessment_scoring":
        routed_agent = "recruiter_screening"

    confidence = 0.95 if known_event else 0.65
    fallback_mode = "safe_default" if known_event else "rule_fallback"
    routing_targets = _routing_targets(routed_agent, state["role"], pathway)
    policy_flags = _policy_flags(state["role"], pathway, sub_intent, confidence, known_event)

    return {
        **state,
        "resolved_intent": resolved_intent,
        "sub_intent": sub_intent,
        "pathway": pathway,
        "routed_agent": routed_agent,
        "routing_targets": routing_targets,
        "confidence": confidence,
        "fallback_mode": fallback_mode,
        "policy_flags": policy_flags,
    }
