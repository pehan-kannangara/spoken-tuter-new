"""
Orchestrator Graph - Main dispatcher orchestrating all agents
"""

from typing import Dict, Any
from sqlalchemy.orm import Session as DBSession

from ..classifier.graph import run_classifier
from ..context_manager.graph import run_context_manager


async def run_orchestration(
    event_type: str,
    payload: Dict[str, Any],
    user_context: Dict[str, Any],
    db: DBSession
) -> Dict[str, Any]:
    """
    Main orchestration pipeline
    
    Args:
        event_type: Type of event to process
        payload: Event payload
        user_context: User context (user_id, email, role)
        db: Database session
        
    Returns:
        Result dictionary with routed_agent, result, and debug metadata
    """
    try:
        # Step 1: Classify intent and route
        classifier_state = await run_classifier(
            event_type=event_type,
            user_id=user_context.get("user_id", "unknown"),
            user_role=user_context.get("role", "learner"),
            payload=payload,
        )
        
        # Convert classifier state to dict for context manager
        classifier_dict = {
            "intent": classifier_state.intent,
            "sub_intent": classifier_state.sub_intent,
            "pathway": classifier_state.pathway,
            "confidence": classifier_state.confidence,
            "fallback_mode": classifier_state.fallback_mode,
            "routing_targets": classifier_state.routing_targets,
            "policy_flags": classifier_state.policy_flags,
        }
        
        # Step 2: Build context package
        context_package = await run_context_manager(
            classifier_state=classifier_dict,
            user_context=user_context,
            payload=payload,
        )
        
        # Step 3: Route to appropriate domain agent
        routed_agent = classifier_state.routing_targets[0] if classifier_state.routing_targets else "unknown"
        
        # For now, return mock result - will be replaced with actual agent calls
        result = {
            "status": "success",
            "message": f"Event routed to {routed_agent}",
            "data": {}
        }
        
        # Build debug metadata
        debug_metadata = {
            "intent": classifier_state.intent,
            "sub_intent": classifier_state.sub_intent,
            "pathway": classifier_state.pathway,
            "confidence": classifier_state.confidence,
            "fallback_mode": classifier_state.fallback_mode,
            "routing_targets": classifier_state.routing_targets,
            "policy_flags": classifier_state.policy_flags,
        }
        
        return {
            "routed_agent": routed_agent,
            "result": result,
            "debug": debug_metadata,
        }
        
    except Exception as e:
        print(f"Orchestration error: {e}")
        return {
            "routed_agent": "error_handler",
            "result": {"error": str(e)},
            "debug": {
                "intent": "error",
                "sub_intent": "unknown",
                "pathway": "unknown",
                "confidence": 0.0,
                "fallback_mode": "error",
                "routing_targets": [],
                "policy_flags": {},
            }
        }
