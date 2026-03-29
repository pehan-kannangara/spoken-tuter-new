"""
Standards Alignment and Elicitation Quality Validators

Standards alignment: Checks if item's predicted difficulty matches target level.
Elicitation quality: Checks if prompt is likely to produce substantive spoken responses.
"""

from backend.qa_engine.config import STANDARDS_ALIGNMENT, ELICITATION_QUALITY
from backend.qa_engine.schemas import QuestionItem, ValidationResult, ValidationGate


def validate_standards_alignment(item: QuestionItem, predicted_level: float | None = None) -> ValidationResult:
    """
    Check: Does item's predicted difficulty match target level?
    
    In production, predicted_level is determined by trained classifier.
    For demo, uses simple heuristics.
    """
    checks = {}
    issues = []
    confidence = 0.80
    
    # Simple heuristic: count complex markers
    instruction = item.instruction.lower()
    
    complexity_markers = {
        "high": ["analyze", "compare", "evaluate", "synthesize", "hypothetical", "implications"],
        "medium": ["explain", "describe", "discuss", "identify", "reason"],
        "low": ["tell", "say", "what", "do", "like"],
    }
    
    high_count = sum(1 for marker in complexity_markers["high"] if marker in instruction)
    medium_count = sum(1 for marker in complexity_markers["medium"] if marker in instruction)
    low_count = sum(1 for marker in complexity_markers["low"] if marker in instruction)
    
    predicted_complexity = "low"
    if high_count > 0:
        predicted_complexity = "high"
    elif medium_count > medium_count / 2:
        predicted_complexity = "medium"
    
    # Map target level to expected complexity (simplified)
    from backend.qa_engine.schemas import TargetLevel, Pathway
    
    target_complexity_map = {
        Pathway.CEFR: {
            TargetLevel.CEFR_A1: "low",
            TargetLevel.CEFR_A2: "low",
            TargetLevel.CEFR_B1: "medium",
            TargetLevel.CEFR_B2: "medium",
            TargetLevel.CEFR_C1: "high",
            TargetLevel.CEFR_C2: "high",
        },
        Pathway.IELTS: {
            TargetLevel.IELTS_3: "low",
            TargetLevel.IELTS_4: "low",
            TargetLevel.IELTS_5: "medium",
            TargetLevel.IELTS_6: "medium",
            TargetLevel.IELTS_7: "high",
            TargetLevel.IELTS_8: "high",
            TargetLevel.IELTS_9: "high",
        },
    }
    
    expected_complexity = target_complexity_map.get(item.pathway, {}).get(item.target_level, "medium")
    
    checks["complexity_matches_level"] = predicted_complexity == expected_complexity
    if not checks["complexity_matches_level"]:
        issues.append(
            f"Predicted complexity '{predicted_complexity}' doesn't match "
            f"expected '{expected_complexity}' for {item.target_level}"
        )
    
    threshold = STANDARDS_ALIGNMENT.get("model_confidence_threshold", 0.85)
    confidence = 0.75 if checks["complexity_matches_level"] else 0.50
    
    overall_pass = checks["complexity_matches_level"]
    
    return ValidationResult(
        gate=ValidationGate.STANDARDS_ALIGNMENT,
        passed=overall_pass,
        confidence=confidence,
        checks_performed=checks,
        issues_found=issues,
        severity="error" if not overall_pass else "info",
        validator_name="standards_alignment_validator",
    )


def validate_elicitation_quality(item: QuestionItem) -> ValidationResult:
    """
    Check: Is prompt likely to elicit substantive spoken responses?
    """
    checks = {}
    issues = []
    confidence = 0.85
    
    instruction = item.instruction.lower()
    
    # Check for open-ended vs closed-ended nature
    open_ended_markers = ["describe", "explain", "tell", "discuss", "think", "feel", "experience", "example"]
    closed_ended_markers = ["what is", "is it", "do you have", "yes or no"]
    
    open_count = sum(1 for marker in open_ended_markers if marker in instruction)
    closed_count = sum(1 for marker in closed_ended_markers if marker in instruction)
    
    checks["open_ended"] = open_count > closed_count
    if not checks["open_ended"]:
        issues.append("Prompt appears closed-ended; may elicit short yes/no responses")
    
    # Check for prompt that invites elaboration
    elaboration_markers = ["why", "how", "what else", "tell more", "give example", "explain further"]
    checks["invites_elaboration"] = any(marker in instruction for marker in elaboration_markers)
    if not checks["invites_elaboration"]:
        issues.append("Prompt doesn't explicitly invite elaboration or examples")
    
    # Check expected response length hint
    # (In production, would use expected_response_template or historical data)
    checks["likely_substantive_response"] = checks["open_ended"] and checks["invites_elaboration"]
    
    overall_pass = checks["likely_substantive_response"]
    
    return ValidationResult(
        gate=ValidationGate.ELICITATION_QUALITY,
        passed=overall_pass,
        confidence=confidence,
        checks_performed=checks,
        issues_found=issues,
        severity="warning" if not overall_pass else "info",
        validator_name="elicitation_quality_validator",
    )


__all__ = ["validate_standards_alignment", "validate_elicitation_quality"]
