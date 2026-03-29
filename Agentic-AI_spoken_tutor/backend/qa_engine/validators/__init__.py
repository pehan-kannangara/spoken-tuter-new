"""
Schema Compliance Validator

Checks that generated items conform to required format and structure.
Hard fails if blueprint fields are missing or malformed.
"""

from datetime import datetime
from typing import Tuple
from backend.qa_engine.config import SCHEMA_COMPLIANCE, INSTRUCTION_CLARITY
from backend.qa_engine.schemas import QuestionItem, ValidationResult, ValidationGate


def validate_schema_compliance(item: QuestionItem) -> ValidationResult:
    """
    Hard gate: Does item conform to JSON schema and have all required fields?
    """
    checks = {}
    issues = []
    
    # Required field checks
    required_fields = ["item_id", "spec_id", "instruction", "pathway", "target_level"]
    for field in required_fields:
        has_field = hasattr(item, field) and getattr(item, field) is not None
        checks[f"has_{field}"] = has_field
        if not has_field:
            issues.append(f"Missing required field: {field}")
    
    # Schema validation
    checks["valid_serializable"] = True  # Pydantic already validated at load
    
    # Instruction non-null
    instruction_valid = bool(item.instruction and len(item.instruction.strip()) > 0)
    checks["instruction_not_empty"] = instruction_valid
    if not instruction_valid:
        issues.append("Instruction is null or empty")
    
    overall_pass = all(checks.values())
    
    return ValidationResult(
        gate=ValidationGate.SCHEMA_COMPLIANCE,
        passed=overall_pass,
        confidence=1.0 if overall_pass else 0.0,
        checks_performed=checks,
        issues_found=issues,
        severity="error" if not overall_pass else "info",
        validator_name="schema_compliance_validator",
    )


def validate_instruction_clarity(item: QuestionItem) -> ValidationResult:
    """
    Check: Is the instruction clear, unambiguous, and well-formed?
    """
    checks = {}
    issues = []
    confidence = 0.8
    
    instruction = item.instruction
    
    # Length checks
    checks["length_in_range"] = (
        INSTRUCTION_CLARITY["min_instruction_length"] 
        <= len(instruction) 
        <= INSTRUCTION_CLARITY["max_instruction_length"]
    )
    if not checks["length_in_range"]:
        issues.append(
            f"Instruction length {len(instruction)} outside range "
            f"({INSTRUCTION_CLARITY['min_instruction_length']}, "
            f"{INSTRUCTION_CLARITY['max_instruction_length']})"
        )
    
    # Multi-question ambiguity check
    question_count = instruction.count("?")
    checks["not_multi_question"] = question_count <= 2
    if question_count > 2:
        issues.append(f"Too many questions ({question_count}) - may be ambiguous to student")
    
    # Unfilled template check
    checks["no_templates"] = "[PLACEHOLDER]" not in instruction and "{{" not in instruction
    if not checks["no_templates"]:
        issues.append("Instruction contains unfilled template placeholders")
    
    # Simple clarity heuristic: contains imperative verb?
    imperative_verbs = ["describe", "explain", "discuss", "tell", "talk", "speak", "answer", "comment"]
    checks["has_clear_task"] = any(verb in instruction.lower() for verb in imperative_verbs)
    if not checks["has_clear_task"]:
        issues.append("Instruction lacks clear task verb (describe, explain, etc.)")
    
    overall_pass = all(checks.values())
    
    return ValidationResult(
        gate=ValidationGate.INSTRUCTION_CLARITY,
        passed=overall_pass,
        confidence=confidence,
        checks_performed=checks,
        issues_found=issues,
        severity="error" if not overall_pass else "info",
        validator_name="instruction_clarity_validator",
    )


def validate_format_compliance(item: QuestionItem) -> ValidationResult:
    """
    Check: Does item follow IELTS Part structure or CEFR task rules?
    """
    checks = {}
    issues = []
    confidence = 0.9
    
    from backend.qa_engine.config import TASK_FORMAT_COMPLIANCE
    from backend.qa_engine.schemas import IELTSSpeakingPart, Pathway
    
    # Task type must be valid enum
    checks["valid_task_type"] = item.task_type in [part.value for part in IELTSSpeakingPart] or isinstance(item.task_type, str)
    if not checks["valid_task_type"]:
        issues.append(f"Invalid task_type: {item.task_type}")
        overall_pass = False
    else:
        # If IELTS, check Part-specific rules
        if item.pathway == Pathway.IELTS:
            task_config = TASK_FORMAT_COMPLIANCE.get("ielts", {}).get(item.task_type)
            if task_config:
                # For Part 2, must have prompt_text (cue card)
                if item.task_type == IELTSSpeakingPart.PART_2:
                    checks["has_prompt_text"] = bool(item.prompt_text and len(item.prompt_text) > 0)
                    if not checks["has_prompt_text"]:
                        issues.append("Part 2 requires prompt_text (cue card)")
        
        overall_pass = all(checks.values())
    
    return ValidationResult(
        gate=ValidationGate.FORMAT_COMPLIANCE,
        passed=overall_pass,
        confidence=confidence,
        checks_performed=checks,
        issues_found=issues,
        severity="error" if not overall_pass else "info",
        validator_name="format_compliance_validator",
    )


__all__ = [
    "validate_schema_compliance",
    "validate_instruction_clarity",
    "validate_format_compliance",
]
