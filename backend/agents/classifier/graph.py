"""
Classifier Agent Graph - Orchestration of classification pipeline
"""

from .state import ClassifierState
from .nodes import classify_node


async def run_classifier(
    event_type: str,
    user_id: str,
    user_role: str,
    payload: dict
) -> ClassifierState:
    """
    Run classifier pipeline
    
    Args:
        event_type: Type of event to classify
        user_id: ID of user making request
        user_role: Role of user
        payload: Request payload
        
    Returns:
        ClassifierState with routing information
    """
    # Initialize state
    state = ClassifierState(
        event_type=event_type,
        user_id=user_id,
        user_role=user_role,
        payload=payload,
    )
    
    # Run classification
    state = classify_node(state)
    
    return state
