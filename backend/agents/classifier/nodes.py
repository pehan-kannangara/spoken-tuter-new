"""
Classifier Agent Nodes - Intent classification logic
"""

from typing import Dict, Any, List
from .state import ClassifierState

# Known pathways for language training
KNOWN_PATHWAYS = {"ielts", "cefr", "business_english"}

# Intent to agent mapping
INTENT_TO_AGENT = {
    "validate_item": "qa_workflow",
    "score_assessment": "assessment_scoring",
    "generate_feedback": "feedback_pathway",
    "create_screening_pack": "recruiter_screening",
    "start_screening_session": "recruiter_screening",
    "submit_screening_response": "recruiter_screening",
    "get_screening_results": "recruiter_screening",
    "manage_class": "feedback_pathway",
    "get_progress": "feedback_pathway",
    "monitor_quality": "qa_workflow",
}

# Sub-intent mapping by event type
EVENT_TO_SUB_INTENT = {
    "validate_item": "quality_assurance",
    "score_assessment": "assessment",
    "generate_feedback": "learning_feedback",
    "create_screening_pack": "talent_screening",
    "start_screening_session": "talent_screening",
    "submit_screening_response": "talent_screening",
    "get_screening_results": "talent_screening",
    "manage_class": "learning_feedback",
    "get_progress": "monitoring",
    "monitor_quality": "quality_assurance",
}


def resolve_pathway(state: ClassifierState) -> str:
    """
    Resolve the learning pathway for the request
    
    Args:
        state: Classifier state
        
    Returns:
        Pathway name (ielts, cefr, or business_english)
    """
    # Recruiter role prefers business_english pathway
    if state.user_role == "recruiter":
        return "business_english"
    
    # Check if pathway is explicitly specified in payload
    if "pathway" in state.payload:
        pathway = state.payload["pathway"]
        if pathway in KNOWN_PATHWAYS:
            return pathway
    
    # Default to business_english for explicit business requests
    if state.event_type in ["create_screening_pack", "start_screening_session", "submit_screening_response", "get_screening_results"]:
        return "business_english"
    
    # Default pathway
    return "business_english"


def resolve_sub_intent(state: ClassifierState) -> str:
    """
    Resolve the sub-intent based on event type
    
    Args:
        state: Classifier state
        
    Returns:
        Sub-intent name
    """
    return EVENT_TO_SUB_INTENT.get(state.event_type, "unknown")


def routing_targets(classifier_state: ClassifierState) -> List[str]:
    """
    Determine which agents should handle this request
    
    Args:
        classifier_state: Current classifier state
        
    Returns:
        List of agent names to route to
    """
    primary_agent = INTENT_TO_AGENT.get(classifier_state.event_type, "unknown")
    targets = [primary_agent] if primary_agent != "unknown" else []
    
    # For high-stakes events, also route to QA workflow
    if classifier_state.event_type in ["score_assessment", "create_screening_pack", "start_screening_session"]:
        if "qa_workflow" not in targets:
            targets.append("qa_workflow")
    
    # For recruiter events, also include recruiter_screening
    if classifier_state.event_type in ["score_assessment"] and classifier_state.user_role == "recruiter":
        if "recruiter_screening" not in targets:
            targets.append("recruiter_screening")
    
    return targets


def policy_flags(classifier_state: ClassifierState) -> Dict[str, Any]:
    """
    Generate policy flags based on event and user context
    
    Args:
        classifier_state: Current classifier state
        
    Returns:
        Dictionary of policy flags
    """
    flags = {
        "require_human_review": False,
        "strict_rubric": False,
        "business_screening_mode": False,
        "known_event": classifier_state.event_type in INTENT_TO_AGENT,
    }
    
    # Recruiter screening is high-stakes - enforce strict rubric
    if classifier_state.user_role == "recruiter":
        flags["strict_rubric"] = True
        flags["business_screening_mode"] = True
    
    # Assessment scoring with recruiter role needs human review
    if classifier_state.event_type == "score_assessment" and classifier_state.user_role == "recruiter":
        flags["require_human_review"] = True
        flags["strict_rubric"] = True
    
    return flags


def classify_node(state: ClassifierState) -> ClassifierState:
    """
    Main classification node - resolves all routing information
    
    Args:
        state: Classifier state
        
    Returns:
        Updated classifier state with routing information
    """
    state.intent = state.event_type
    state.sub_intent = resolve_sub_intent(state)
    state.pathway = resolve_pathway(state)
    state.routing_targets = routing_targets(state)
    state.policy_flags = policy_flags(state)
    state.confidence = 0.95 if state.event_type in INTENT_TO_AGENT else 0.5
    state.fallback_mode = "safe_default" if state.confidence < 0.8 else "strict"
    
    return state
