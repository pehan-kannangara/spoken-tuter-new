from backend.agents.classifier.graph import run_classifier
from backend.agents.context_manager.graph import run_context_manager
from backend.agents.assessment_scoring.graph import run_assessment_scoring
from backend.agents.feedback_pathway.graph import run_feedback_pathway
from backend.agents.recruiter_screening.graph import run_recruiter_screening
from backend.agents.monitoring_analytics.graph import run_monitoring_analytics
from backend.agents.qa_workflow.graph import run_qa_workflow


def run_orchestration(user_id: str, role: str, event_type: str, payload: dict) -> dict:
    classifier_state = run_classifier(
        user_id=user_id,
        role=role,
        event_type=event_type,
        payload=payload,
    )

    context_state = run_context_manager(
        user_id=user_id,
        role=role,
        classifier_state=classifier_state,
        payload=payload,
    )

    routed_agent = classifier_state["routed_agent"]

    if routed_agent == "assessment_scoring":
        domain_result = run_assessment_scoring(user_id, payload, context_state["context"])
    elif routed_agent == "feedback_pathway":
        domain_result = run_feedback_pathway(user_id, payload, context_state["context"])
    elif routed_agent == "recruiter_screening":
        domain_result = run_recruiter_screening(user_id, payload, context_state["context"])
    elif routed_agent == "qa_workflow":
        domain_result = run_qa_workflow(user_id, event_type, payload, context_state["context"])
    else:
        domain_result = run_monitoring_analytics(user_id, payload, context_state["context"])

    return {
        "status": "ok",
        "routed_agent": routed_agent,
        "message": domain_result.get("message", "Workflow executed"),
        "debug": {
            "intent": classifier_state["resolved_intent"],
            "sub_intent": classifier_state.get("sub_intent"),
            "pathway": classifier_state.get("pathway"),
            "confidence": classifier_state["confidence"],
            "fallback_mode": classifier_state.get("fallback_mode"),
            "routing_targets": classifier_state.get("routing_targets", []),
            "policy_flags": classifier_state.get("policy_flags", {}),
        },
    }
