from backend.agents.classifier.state import ClassifierState


INTENT_TO_AGENT = {
    "start_initial_assessment": "assessment_scoring",
    "submit_assessment_part": "assessment_scoring",
    "view_feedback": "feedback_pathway",
    "view_learning_pathway": "feedback_pathway",
    "create_screening_pack": "recruiter_screening",
    "send_candidate_assessment": "recruiter_screening",
    "view_class_analytics": "monitoring_analytics",
    "scheduled_risk_check": "monitoring_analytics",
    # QA Engine Events (Item Generation, Validation, Lifecycle Management)
    "generate_item": "qa_workflow",
    "validate_item": "qa_workflow",
    "activate_item": "qa_workflow",
    "monitor_drift": "qa_workflow",
    "retire_item": "qa_workflow",
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
