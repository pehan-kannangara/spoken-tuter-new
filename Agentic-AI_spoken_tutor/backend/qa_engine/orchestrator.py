"""
QA Orchestrator

Master workflow that runs all validators in sequence and produces
comprehensive quality report with pass/fail decision.
"""

import uuid
from datetime import datetime
from typing import Optional

from backend.qa_engine.config import (
    AUTO_PUBLISH, 
    QUALITY_SCORE_WEIGHTS, 
    ValidationGate,
    ItemStatus
)
from backend.qa_engine.schemas import (
    QuestionItem,
    QAValidationReport,
    ValidationResult,
    ItemStatus as ItemStatusEnum,
)
from backend.qa_engine.validators import (
    validate_schema_compliance,
    validate_instruction_clarity,
    validate_format_compliance,
)
from backend.qa_engine.validators.bias_safety import validate_bias_safety
from backend.qa_engine.validators.duplicate_check import validate_duplicate_check
from backend.qa_engine.validators.standards_elicitation import (
    validate_standards_alignment,
    validate_elicitation_quality,
)


def _gate_name(gate: object) -> str:
    return str(getattr(gate, "value", gate))


def run_qa_validation_pipeline(
    item: QuestionItem,
    existing_active_items: list[QuestionItem] | None = None,
    run_all_gates: bool = True,
    user_id: str = "system",
) -> QAValidationReport:
    """
    Execute complete QA validation pipeline on a generated question item.
    
    Args:
        item: The question item to validate
        existing_active_items: List of active items for duplicate checking
        run_all_gates: If True, run all validators. If False, stop at first failure.
        user_id: User/system triggering this validation
    
    Returns:
        QAValidationReport with gate results and overall recommendation
    """
    
    report_id = str(uuid.uuid4())
    validation_results: list[ValidationResult] = []
    
    # Run validators in sequence
    # Note: These are deterministic checks, so order matters for efficiency
    
    # Gate 1: Schema Compliance (hard fail)
    schema_result = validate_schema_compliance(item)
    validation_results.append(schema_result)
    if not schema_result.passed and not run_all_gates:
        # Hard stop if schema fails
        return _create_report(
            report_id,
            item,
            validation_results,
            user_id,
            is_schema_failed=True
        )
    
    # Gate 2: Instruction Clarity
    clarity_result = validate_instruction_clarity(item)
    validation_results.append(clarity_result)
    if not clarity_result.passed and not run_all_gates:
        return _create_report(report_id, item, validation_results, user_id)
    
    # Gate 3: Format Compliance
    format_result = validate_format_compliance(item)
    validation_results.append(format_result)
    if not format_result.passed and not run_all_gates:
        return _create_report(report_id, item, validation_results, user_id)
    
    # Gate 4: Bias & Safety
    bias_result = validate_bias_safety(item)
    validation_results.append(bias_result)
    if not bias_result.passed and not run_all_gates:
        return _create_report(report_id, item, validation_results, user_id)
    
    # Gate 5: Duplicate Check
    dup_result = validate_duplicate_check(item, existing_active_items or [])
    validation_results.append(dup_result)
    if not dup_result.passed and not run_all_gates:
        return _create_report(report_id, item, validation_results, user_id)
    
    # Gate 6: Standards Alignment
    align_result = validate_standards_alignment(item)
    validation_results.append(align_result)
    if not align_result.passed and not run_all_gates:
        return _create_report(report_id, item, validation_results, user_id)
    
    # Gate 7: Elicitation Quality
    elicit_result = validate_elicitation_quality(item)
    validation_results.append(elicit_result)
    
    # All gates complete; compute overall decision
    return _create_report(report_id, item, validation_results, user_id)


def _create_report(
    report_id: str,
    item: QuestionItem,
    validation_results: list[ValidationResult],
    user_id: str,
    is_schema_failed: bool = False,
) -> QAValidationReport:
    """
    Compute overall pass/fail and quality score based on gate results.
    """
    
    # Check if all required gates passed
    required_gates = {_gate_name(gate) for gate in AUTO_PUBLISH.get("required_gates", [])}
    
    gate_by_name = {_gate_name(result.gate): result for result in validation_results}
    
    all_required_passed = all(
        gate_by_name.get(gate, ValidationResult(
            gate=gate,
            passed=False,
            confidence=0.0,
            checks_performed={},
            issues_found=["Gate not run"],
            severity="error",
            validator_name="unknown",
        )).passed
        for gate in required_gates
    )
    
    overall_pass = all_required_passed
    
    # Compute composite quality score (0-100)
    gate_scores = {}
    for result in validation_results:
        # Each passing gate contributes to score
        gate_name = _gate_name(result.gate)
        gate_scores[gate_name] = 100.0 if result.passed else 0.0
    
    # Weighted average
    if gate_scores:
        total_weight = sum(QUALITY_SCORE_WEIGHTS.get(g.replace("_", "_"), 0.1) for g in gate_scores)
        quality_score = (
            sum(
                gate_scores.get(g, 0.0) * QUALITY_SCORE_WEIGHTS.get(g.replace("_", "_"), 0.1)
                for g in gate_scores
            )
            / total_weight
            if total_weight > 0
            else 0.0
        )
    else:
        quality_score = 0.0
    
    # Determine recommendation
    if is_schema_failed:
        recommended_action = "reject"
        next_stage = None
    elif overall_pass:
        recommended_action = "accept"
        next_stage = ItemStatusEnum.AUTO_VALIDATED
    elif quality_score >= 70:
        recommended_action = "review"  # Expert review needed
        next_stage = ItemStatusEnum.EXPERT_REVIEW_PENDING
    else:
        recommended_action = "reject"
        next_stage = None
    
    # Collect issues by severity
    critical_issues = [
        issue
        for result in validation_results
        if result.severity == "error"
        for issue in result.issues_found
    ]
    
    warnings = [
        issue
        for result in validation_results
        if result.severity == "warning"
        for issue in result.issues_found
    ]
    
    report = QAValidationReport(
        report_id=report_id,
        item_id=item.item_id,
        validation_results=validation_results,
        overall_pass=overall_pass,
        quality_score=quality_score,
        recommended_action=recommended_action,
        critical_issues=critical_issues,
        warnings=warnings,
        next_stage_if_accepted=next_stage,
        created_at=datetime.utcnow(),
        created_by=user_id,
    )
    
    return report


def should_auto_activate(report: QAValidationReport) -> bool:
    """
    Determine if item should immediately move to ACTIVE state.
    Based on AUTO_PUBLISH config.
    """
    return (
        report.overall_pass 
        and report.quality_score >= 85
        and AUTO_PUBLISH.get("auto_activate_on_pass", False)
    )


__all__ = ["run_qa_validation_pipeline", "should_auto_activate"]
