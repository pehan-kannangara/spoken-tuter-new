"""
Assessment Scoring Agent Graph - Orchestration of scoring pipeline
"""

from typing import Dict, Any
from sqlalchemy.orm import Session as DBSession

from .state import AssessmentScoringState
from .nodes import (
    run_quality_gates,
    calculate_raw_score,
    apply_rubric_policy,
    prepare_response,
)
from ...stores.assessment_store import AssessmentStore


async def run_assessment_scoring(
    context_package: Dict[str, Any],
    payload: Dict[str, Any],
    db: DBSession,
) -> Dict[str, Any]:
    """
    Run assessment scoring pipeline
    
    Args:
        context_package: Full context from context manager
        payload: Event payload with assessment_id, response_id, etc.
        db: Database session
        
    Returns:
        Result with score, quality_decision, and gates results
    """
    try:
        # Initialize state
        state = AssessmentScoringState(
            assessment_id=payload.get("assessment_id", ""),
            response_id=payload.get("response_id", ""),
            question_id=payload.get("question_id", ""),
            response_text=payload.get("response_text", ""),
            learner_id=payload.get("learner_id", ""),
            context_package=context_package,
        )
        
        # Step 1: Run quality gates
        state = run_quality_gates(state)
        
        # Step 2: Calculate raw score
        state = calculate_raw_score(state)
        
        # Step 3: Apply rubric policy
        state = apply_rubric_policy(state)
        
        # Step 4: Prepare response
        state = prepare_response(state)
        
        # Step 5: Persist results
        assessment_store = AssessmentStore(db)
        
        # Update response with score
        if state.response_id:
            assessment_store.update_response_score(
                response_id=state.response_id,
                score=state.final_score,
                schema_passed="schema_validation" in state.gates_passed,
                clarity_passed="clarity_check" in state.gates_passed,
                format_passed="format_validation" in state.gates_passed,
                bias_passed="bias_check" in state.gates_passed,
            )
        
        # Update assessment with final score
        if state.assessment_id:
            assessment_store.update_assessment_score(
                assessment_id=state.assessment_id,
                final_score=state.final_score,
                quality_decision=state.quality_decision,
                rubric_applied=state.rubric_applied,
            )
        
        return {
            "status": "success",
            "assessment_id": state.assessment_id,
            "response_id": state.response_id,
            "final_score": round(state.final_score, 2),
            "quality_score": round(state.quality_score, 2),
            "quality_decision": state.quality_decision,
            "rubric_applied": state.rubric_applied,
            "gates_passed": state.gates_passed,
            "gates_failed": state.gates_failed,
            "feedback": generate_feedback(state),
        }
        
    except Exception as e:
        print(f"Assessment scoring error: {e}")
        return {
            "status": "error",
            "error": str(e),
            "final_score": 0,
            "quality_decision": "error",
        }


def generate_feedback(state: AssessmentScoringState) -> str:
    """
    Generate human-readable feedback for learner
    
    Args:
        state: Assessment scoring state
        
    Returns:
        Feedback string
    """
    feedbacks = []
    
    # Score-based feedback
    if state.final_score >= 85:
        feedbacks.append("Excellent response! Strong performance.")
    elif state.final_score >= 70:
        feedbacks.append("Good work! You're on the right track.")
    elif state.final_score >= 50:
        feedbacks.append("Fair attempt. With some practice, you can improve.")
    else:
        feedbacks.append("This needs more work. Try to focus on clarity and structure.")
    
    # Gate-specific feedback
    if "clarity_check" in state.gates_failed:
        feedbacks.append("Try to be clearer in your expression. Use simpler, more structured sentences.")
    
    if "response_length" in state.gates_failed:
        feedbacks.append("Your response may be too short or too long. Aim for a balanced length.")
    
    if "schema_validation" in state.gates_failed:
        feedbacks.append("Make sure your response follows the expected format and structure.")
    
    # Quality decision feedback
    if state.quality_decision == "rejected":
        feedbacks.append("This response does not meet the minimum quality threshold. Please try again.")
    elif state.quality_decision == "requires_review":
        feedbacks.append("This response needs human review for a final decision.")
    
    return " ".join(feedbacks)
