"""
Duplicate Detection Validator

Checks for semantic similarity and token overlap with existing active items.
Prevents near-duplicate items in the bank.
"""

from backend.qa_engine.config import DUPLICATE_CHECK
from backend.qa_engine.schemas import QuestionItem, ValidationResult, ValidationGate


def simple_token_overlap(text1: str, text2: str) -> float:
    """
    Simple token overlap ratio (Jaccard-like).
    Returns float 0-1.
    """
    tokens1 = set(text1.lower().split())
    tokens2 = set(text2.lower().split())
    
    if not tokens1 or not tokens2:
        return 0.0
    
    intersection = len(tokens1 & tokens2)
    union = len(tokens1 | tokens2)
    
    return intersection / union if union > 0 else 0.0


def validate_duplicate_check(
    item: QuestionItem, 
    existing_active_items: list[QuestionItem] | None = None
) -> ValidationResult:
    """
    Check: Is this item too similar to existing active items?
    
    In production, existing_active_items would be fetched from DB.
    For demo, defaults to empty list.
    """
    checks = {}
    issues = []
    confidence = 0.95
    
    if not existing_active_items:
        existing_active_items = []
    
    # Combine instruction + prompt for similarity
    item_text = f"{item.instruction} {item.prompt_text or ''}".strip()
    
    max_overlap = 0.0
    most_similar_item = None
    
    for existing in existing_active_items:
        # Only compare within same level/pathway for efficiency
        if existing.pathway != item.pathway or existing.target_level != item.target_level:
            continue
        
        existing_text = f"{existing.instruction} {existing.prompt_text or ''}".strip()
        
        overlap = simple_token_overlap(item_text, existing_text)
        if overlap > max_overlap:
            max_overlap = overlap
            most_similar_item = existing
    
    threshold = DUPLICATE_CHECK.get("token_overlap_threshold", 0.70)
    checks["not_duplicate"] = max_overlap < threshold
    
    if not checks["not_duplicate"]:
        issues.append(
            f"Token overlap {max_overlap:.2f} exceeds threshold {threshold}. "
            f"Similar to item: {most_similar_item.item_id if most_similar_item else 'unknown'}"
        )
    
    overall_pass = checks["not_duplicate"]
    
    return ValidationResult(
        gate=ValidationGate.DUPLICATE_CHECK,
        passed=overall_pass,
        confidence=confidence,
        checks_performed=checks,
        issues_found=issues,
        severity="error" if not overall_pass else "info",
        validator_name="duplicate_check_validator",
    )


__all__ = ["validate_duplicate_check", "simple_token_overlap"]
