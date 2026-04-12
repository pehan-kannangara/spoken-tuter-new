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


def classify_intent(state: ClassifierState) -> ClassifierState:
    event_type = state["event_type"]
    resolved_intent = event_type
    routed_agent = INTENT_TO_AGENT.get(event_type, "assessment_scoring")
    confidence = 0.95 if event_type in INTENT_TO_AGENT else 0.60

    return {
        **state,
        "resolved_intent": resolved_intent,
        "routed_agent": routed_agent,
        "confidence": confidence,
    }
