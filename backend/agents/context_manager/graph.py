"""
Context Manager Graph - Orchestration of context package building
"""

from typing import Dict, Any
from .state import ContextManagerState, ContextPackage
from .nodes import context_manager_node


async def run_context_manager(
    classifier_state: Dict[str, Any],
    user_context: Dict[str, Any],
    payload: Dict[str, Any]
) -> ContextPackage:
    """
    Run context manager pipeline
    
    Args:
        classifier_state: State from classifier
        user_context: User context from auth
        payload: Original request payload
        
    Returns:
        ContextPackage with full context
    """
    # Initialize state
    state = ContextManagerState(
        classifier_state=classifier_state,
        user_context=user_context,
        payload=payload,
    )
    
    # Run context manager
    state = context_manager_node(state)
    
    return state.context_package
