"""
Assessment Scoring Agent Nodes - Scoring logic and quality gates
"""

import re
from typing import Dict, Any
from .state import AssessmentScoringState


# Quality gates scoring weights
QUALITY_GATE_WEIGHTS = {
    "schema_validation": 0.1,      # 10%
    "clarity_check": 0.15,         # 15%
    "format_validation": 0.15,     # 15%
    "bias_check": 0.1,             # 10%
    "response_length": 0.15,       # 15%
    "grammar_check": 0.15,         # 15%
    "fluency_check": 0.15,         # 15%
}


def run_schema_validation(response_text: str) -> tuple[bool, float]:
    """
    Validate response has required structure/format
    
    Returns: (passed, score_contribution)
    """
    # Check minimum length
    if len(response_text.strip()) < 10:
        return False, 0.0
    
    # Check has sentences
    sentences = re.split(r'[.!?]+', response_text.strip())
    if len([s for s in sentences if s.strip()]) < 1:
        return False, 0.0
    
    return True, 1.0


def run_clarity_check(response_text: str) -> tuple[bool, float]:
    """
    Check response clarity and coherence
    
    Returns: (passed, score_contribution)
    """
    # Simple clarity metrics
    avg_sentence_length = len(response_text) / max(len(re.split(r'[.!?]+', response_text)), 1)
    
    # Very short or very long sentences indicate clarity issues
    if avg_sentence_length < 5 or avg_sentence_length > 50:
        return False, 0.5
    
    # Check for common filler words (indication of unclear thinking)
    filler_words = ["um", "uh", "like", "basically"]
    filler_count = sum(1 for word in filler_words if f" {word} " in f" {response_text.lower()} ")
    
    if filler_count > 5:
        return False, 0.6
    
    return True, 0.9 - (filler_count * 0.05)


def run_format_validation(response_text: str) -> tuple[bool, float]:
    """
    Check response format and punctuation
    
    Returns: (passed, score_contribution)
    """
    # Check for proper punctuation
    has_period = "." in response_text
    has_question_mark = "?" in response_text
    
    # At least one sentence should end properly
    if not (has_period or has_question_mark):
        return False, 0.5
    
    # Check capitalization
    starts_capitalized = response_text[0].isupper() if response_text else False
    
    score = 0.9 if starts_capitalized else 0.7
    return True, score


def run_bias_check(response_text: str) -> tuple[bool, float]:
    """
    Check for potential bias, offensive language, etc.
    
    Returns: (passed, score_contribution)
    """
    # Simple check for common offensive patterns
    offensive_words = ["hate", "stupid", "dumb", "idiot"]
    response_lower = response_text.lower()
    
    offensive_count = sum(1 for word in offensive_words if word in response_lower)
    
    if offensive_count > 0:
        return False, 0.0
    
    return True, 1.0


def run_response_length_check(response_text: str) -> tuple[bool, float]:
    """
    Check response is adequate length
    
    Returns: (passed, score_contribution)
    """
    word_count = len(response_text.split())
    
    # Ideal range: 20-200 words for short response
    if word_count < 10:
        return False, word_count / 10.0 if word_count > 0 else 0.0
    elif word_count < 20:
        score = 0.6 + (word_count - 10) * 0.04
        return False, score
    elif word_count > 500:
        return False, 0.7  # Too long
    
    return True, 1.0


def run_quality_gates(state: AssessmentScoringState) -> AssessmentScoringState:
    """
    Run all quality gates on response
    
    Args:
        state: Assessment scoring state
        
    Returns:
        Updated state with gate results
    """
    response_text = state.response_text
    
    # Run gates
    gates = {
        "schema_validation": run_schema_validation(response_text),
        "clarity_check": run_clarity_check(response_text),
        "format_validation": run_format_validation(response_text),
        "bias_check": run_bias_check(response_text),
        "response_length": run_response_length_check(response_text),
    }
    
    # Track results
    quality_score = 0.0
    for gate_name, (passed, score_contribution) in gates.items():
        gate_weight = QUALITY_GATE_WEIGHTS.get(gate_name, 0.1)
        quality_score += score_contribution * gate_weight
        
        if passed:
            state.gates_passed.append(gate_name)
        else:
            state.gates_failed.append(gate_name)
    
    state.quality_score = quality_score * 100  # Convert to 0-100 scale
    
    return state


def calculate_raw_score(state: AssessmentScoringState) -> AssessmentScoringState:
    """
    Calculate raw assessment score
    
    In production, this would call an LLM or rubric engine.
    For now, we use quality score as proxy.
    
    Args:
        state: Assessment scoring state
        
    Returns:
        Updated state with raw_score
    """
    # Use quality score as base
    state.raw_score = state.quality_score
    
    # In real system, would call LLM here:
    # llm_score = await llm_service.score_response(state.response_text, rubric)
    # state.raw_score = (state.quality_score * 0.4) + (llm_score * 0.6)
    
    return state


def apply_rubric_policy(state: AssessmentScoringState) -> AssessmentScoringState:
    """
    Apply rubric policy based on context
    
    Args:
        state: Assessment scoring state
        
    Returns:
        Updated state with quality decision
    """
    # Get context quality policy
    context = state.context_package or {}
    quality_policy = context.get("quality_policy", {})
    strict_rubric = quality_policy.get("strict_rubric", False)
    minimum_quality_score = quality_policy.get("minimum_quality_score", 70)
    require_human_review = quality_policy.get("require_human_review", False)
    
    # Determine quality decision
    if state.raw_score >= minimum_quality_score:
        state.quality_decision = "accepted"
    elif state.raw_score >= (minimum_quality_score - 15):
        state.quality_decision = "requires_review" if not strict_rubric else "rejected"
    else:
        state.quality_decision = "rejected"
    
    # If human review required, escalate
    if require_human_review:
        state.quality_decision = "requires_review"
    
    state.rubric_applied = True
    state.final_score = state.raw_score
    
    return state


def prepare_response(state: AssessmentScoringState) -> AssessmentScoringState:
    """
    Prepare final response for return to API
    
    Args:
        state: Assessment scoring state
        
    Returns:
        Updated state ready for API response
    """
    if state.final_score is None:
        state.final_score = state.raw_score or 0.0
    
    return state
