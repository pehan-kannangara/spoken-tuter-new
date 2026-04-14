"""
Context Manager Nodes - Context package building logic
"""

from typing import Dict, Any
from datetime import datetime
from .state import (
    ContextManagerState, ContextPackage, ActorProfile, WorkflowIntent,
    QualityPolicy, ScreeningPolicy, ExecutionConstraints
)


def build_context_package(state: ContextManagerState) -> ContextPackage:
    """
    Build complete context package from classifier output and user context
    
    Args:
        state: ContextManagerState
        
    Returns:
        ContextPackage with all context information
    """
    classifier = state.classifier_state
    user_ctx = state.user_context
    payload = state.payload
    
    # Build actor profile
    actor = ActorProfile(
        user_id=user_ctx.get("user_id", "unknown"),
        role=user_ctx.get("role", "learner"),
        email=user_ctx.get("email"),
        pathway=classifier.get("pathway", "business_english"),
    )
    
    # Build workflow intent
    workflow = WorkflowIntent(
        intent=classifier.get("intent", "unknown"),
        sub_intent=classifier.get("sub_intent", "unknown"),
        confidence=classifier.get("confidence", 0.5),
    )
    
    # Build quality policy
    policy_flags = classifier.get("policy_flags", {})
    quality_policy = QualityPolicy(
        strict_rubric=policy_flags.get("strict_rubric", False),
        require_human_review=policy_flags.get("require_human_review", False),
        minimum_quality_score=85 if policy_flags.get("strict_rubric") else 70,
    )
    
    # Build screening policy
    screening_policy = ScreeningPolicy(
        business_screening_mode=policy_flags.get("business_screening_mode", False),
        preferred_domains=["business"] if policy_flags.get("business_screening_mode") else [],
        job_level=payload.get("job_level"),
    )
    
    # Build execution constraints
    constraints = ExecutionConstraints(
        max_attempts=3,
        timeout_seconds=300,
        require_approval=policy_flags.get("require_human_review", False),
    )
    
    # Build intent history
    intent_history = [classifier.get("intent", "unknown")]
    
    # Build context package
    context_package = ContextPackage(
        actor=actor,
        workflow=workflow,
        quality_policy=quality_policy,
        screening_policy=screening_policy,
        constraints=constraints,
        intent_history=intent_history,
        metadata={
            "routed_targets": classifier.get("routing_targets", []),
            "fallback_mode": classifier.get("fallback_mode", "safe_default"),
            "policy_flags": policy_flags,
            "original_payload": payload,
        }
    )
    
    return context_package


def context_manager_node(state: ContextManagerState) -> ContextManagerState:
    """
    Main context manager node - builds context package
    
    Args:
        state: ContextManagerState
        
    Returns:
        Updated state with context package
    """
    state.context_package = build_context_package(state)
    return state
