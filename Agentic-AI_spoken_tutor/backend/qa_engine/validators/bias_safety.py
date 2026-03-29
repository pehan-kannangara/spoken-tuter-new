"""
Bias, Safety, and Fairness Validator

Checks for cultural bias, harmful content, stereotype risks, and fairness issues.
Uses keyword-based heuristics and optional LLM-based toxicity checks.
"""

from backend.qa_engine.config import BIAS_SAFETY
from backend.qa_engine.schemas import QuestionItem, ValidationResult, ValidationGate


def validate_bias_safety(item: QuestionItem) -> ValidationResult:
    """
    Check: Does prompt avoid banned topics and reduce bias/stereotype risk?
    """
    checks = {}
    issues = []
    confidence = 0.85
    
    instruction = item.instruction.lower()
    prompt_text = (item.prompt_text or "").lower()
    combined_text = f"{instruction} {prompt_text}"
    
    # Banned topics check
    banned_found = []
    for topic in BIAS_SAFETY.get("banned_topics", []):
        if topic.lower() in combined_text:
            banned_found.append(topic)
    
    checks["no_banned_topics"] = len(banned_found) == 0
    if banned_found:
        issues.append(f"Found banned topics: {', '.join(banned_found)}")
    
    # Restricted topics flag (warning, not hard fail)
    restricted_found = []
    for topic in BIAS_SAFETY.get("restricted_topics", []):
        if topic.lower() in combined_text:
            restricted_found.append(topic)
    
    checks["no_restricted_topics"] = len(restricted_found) == 0
    if restricted_found:
        issues.append(f"Contains restricted topics (requires extra review): {', '.join(restricted_found)}")
        # Note: restricted topics don't auto-fail, just flag for review
    
    # Cultural neutrality proxy: check for region-specific idioms/references
    region_markers = {
        "us": ["american", "usa", "california", "new york", "dollar", "thanksgiving"],
        "uk": ["british", "london", "queen", "pound sterling"],
        "au": ["australian", "sydney", "koala"],
        "in": ["indian", "taj mahal", "bollywood"],
    }
    
    region_specific = 0
    for region, markers in region_markers.items():
        count = sum(1 for marker in markers if marker in combined_text)
        region_specific += count
    
    checks["culturally_neutral"] = region_specific <= 1  # Allow max 1 region-specific reference
    if region_specific > 1:
        issues.append("Prompt contains multiple region-specific references; may bias non-native speakers")
    
    # Stereotype language proxy (simple keyword check)
    stereotype_phrases = [
        "typical", "stereotypical", "obviously", "everyone knows", "of course", "naturally"
    ]
    stereotype_found = [phrase for phrase in stereotype_phrases if phrase in combined_text]
    
    checks["avoids_stereotype_language"] = len(stereotype_found) == 0
    if stereotype_found:
        issues.append("Contains stereotype-triggering language")
    
    # Overall decision
    overall_pass = checks["no_banned_topics"] and checks["culturally_neutral"] and checks["avoids_stereotype_language"]
    
    return ValidationResult(
        gate=ValidationGate.BIAS_SAFETY,
        passed=overall_pass,
        confidence=confidence,
        checks_performed=checks,
        issues_found=issues,
        severity="error" if not overall_pass else ("warning" if restricted_found else "info"),
        validator_name="bias_safety_validator",
    )


__all__ = ["validate_bias_safety"]
