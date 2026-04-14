"""
QA Agent Graph

LangGraph-based orchestration for QA workflows.
Integrates item generation, validation, calibration, and monitoring.
"""

from datetime import datetime
import uuid

from backend.qa_engine.config import ItemStatus
from backend.qa_engine.schemas import (
    QuestionItem,
)
from backend.qa_engine.orchestrator import run_qa_validation_pipeline, should_auto_activate
from backend.qa_engine.lifecycle import create_lifecycle, apply_validation_report, transition_item
from backend.qa_engine.store import (
    get_item,
    get_lifecycle,
    list_active_items,
    save_item,
    save_lifecycle,
    save_report,
)


def _apply_rubric_policy(report, context: dict):
    policy = context.get("quality_policy", {}) if isinstance(context, dict) else {}
    strict_rubric = bool(policy.get("strict_rubric", False))
    require_human_review = bool(policy.get("require_human_review", False))
    minimum_quality_score = float(policy.get("minimum_quality_score", 70.0))

    failed_required = [str(getattr(result.gate, "value", result.gate)) for result in report.validation_results if not result.passed]
    hard_gate_failed = bool(failed_required)

    adjusted_action = report.recommended_action
    adjusted_overall_pass = report.overall_pass

    if hard_gate_failed or report.quality_score < minimum_quality_score:
        adjusted_overall_pass = False
        adjusted_action = "review" if report.quality_score >= 60 else "reject"

    if strict_rubric and report.quality_score < 85 and adjusted_action == "accept":
        adjusted_overall_pass = False
        adjusted_action = "review"

    if require_human_review and adjusted_action == "accept":
        adjusted_overall_pass = False
        adjusted_action = "review"

    if adjusted_action == report.recommended_action and adjusted_overall_pass == report.overall_pass:
        return report, {
            "strict_rubric": strict_rubric,
            "require_human_review": require_human_review,
            "minimum_quality_score": minimum_quality_score,
            "hard_gate_failed": hard_gate_failed,
            "failed_required_gates": failed_required,
            "adjusted": False,
        }

    updated_report = report.model_copy(
        update={
            "overall_pass": adjusted_overall_pass,
            "recommended_action": adjusted_action,
        }
    )
    return updated_report, {
        "strict_rubric": strict_rubric,
        "require_human_review": require_human_review,
        "minimum_quality_score": minimum_quality_score,
        "hard_gate_failed": hard_gate_failed,
        "failed_required_gates": failed_required,
        "adjusted": True,
    }


def run_qa_workflow(user_id: str, event_type: str, payload: dict, context: dict) -> dict:
    """
    Entry point for QA workflows.
    Routes to specific QA handlers based on event_type.
    """
    
    if event_type == "generate_item":
        return handle_generate_item(user_id, payload, context)
    elif event_type == "validate_item":
        return handle_validate_item(user_id, payload, context)
    elif event_type == "activate_item":
        return handle_activate_item(user_id, payload, context)
    elif event_type == "monitor_drift":
        return handle_monitor_drift(user_id, payload, context)
    elif event_type == "retire_item":
        return handle_retire_item(user_id, payload, context)
    else:
        return {
            "status": "error",
            "message": f"Unknown QA event type: {event_type}",
            "user_id": user_id,
        }


def handle_generate_item(user_id: str, payload: dict, context: dict) -> dict:
    """
    Generate a new question item from specification.
    
    Payload:
        - spec_id: Specification ID
        - spec_data: ItemSpecification dict
        - generation_method: "template" | "llm" | "hybrid"
    
    Returns:
        - Generated QuestionItem
        - Empty lifecycle (DRAFT status)
    """
    
    spec_id = payload.get("spec_id", str(uuid.uuid4()))
    spec_data = payload.get("spec_data")
    generation_method = payload.get("generation_method", "template")
    
    if not spec_data:
        return {
            "status": "error",
            "message": "spec_data required in payload",
            "user_id": user_id,
        }
    
    # MVP generation: deterministic starter prompt. This will be replaced by LLM generation.
    instruction = payload.get(
        "instruction",
        f"Describe your experience with {spec_data.get('domain', 'this topic')} and explain your main opinion.",
    )
    prompt_text = payload.get("prompt_text")
    if spec_data.get("task_type") == "part_2" and not prompt_text:
        prompt_text = "You should say: what happened, where it happened, who was involved, and why it was meaningful."
    
    item = QuestionItem(
        item_id=str(uuid.uuid4()),
        spec_id=spec_id,
        instruction=instruction,
        prompt_text=prompt_text,
        pathway=spec_data.get("pathway"),
        target_level=spec_data.get("target_level"),
        task_type=spec_data.get("task_type"),
        domain=spec_data.get("domain"),
        skill_focus=spec_data.get("skill_focus", "mixed"),
        generated_by=generation_method,
        generation_timestamp=datetime.utcnow(),
        status=ItemStatus.DRAFT.value,
    )
    
    lifecycle = create_lifecycle(item, user_id)
    save_item(item)
    save_lifecycle(lifecycle)
    
    return {
        "status": "ok",
        "message": f"Item generated: {item.item_id}",
        "item_id": item.item_id,
        "item": item.dict(),
        "lifecycle": lifecycle.dict(),
        "next_step": "validate_item",
    }


def handle_validate_item(user_id: str, payload: dict, context: dict) -> dict:
    """
    Validate a generated item through quality gates.
    
    Payload:
        - item_id: Item to validate
        - item_data: QuestionItem dict
        - existing_item_ids: List of active item IDs for duplicate check
    
    Returns:
        - QAValidationReport
        - Recommended next action
    """
    
    item_id = payload.get("item_id")
    item_data = payload.get("item_data")
    item = None
    if item_id:
        item = get_item(item_id)
    elif item_data:
        item = QuestionItem(**item_data)

    if not item:
        return {
            "status": "error",
            "message": "item_id or item_data required",
            "user_id": user_id,
        }

    lifecycle = get_lifecycle(item.item_id)
    if not lifecycle:
        return {
            "status": "error",
            "message": f"Lifecycle not found for item: {item.item_id}",
            "user_id": user_id,
        }

    existing_items = list_active_items(exclude_item_id=item.item_id)
    
    # Run validation pipeline
    report = run_qa_validation_pipeline(
        item=item,
        existing_active_items=existing_items,
        run_all_gates=True,
        user_id=user_id,
    )
    report, rubric_decision = _apply_rubric_policy(report, context)
    save_report(report)

    transitioned, transition_message, updated_lifecycle = apply_validation_report(
        lifecycle=lifecycle,
        report=report,
        user_id=user_id,
    )
    if transitioned:
        save_lifecycle(updated_lifecycle)
    
    # Determine next action
    if report.overall_pass:
        next_step = "activate_item" if should_auto_activate(report) else "expert_review"
    else:
        next_step = "reject_item" if report.recommended_action == "reject" else "expert_review"
    
    return {
        "status": "ok",
        "message": f"Validation complete. Quality score: {report.quality_score:.1f}/100",
        "item_id": item.item_id,
        "report_id": report.report_id,
        "report": report.dict(),
        "recommended_action": report.recommended_action,
        "next_step": next_step,
        "quality_score": report.quality_score,
        "lifecycle_transitioned": transitioned,
        "lifecycle_message": transition_message,
        "current_status": getattr(updated_lifecycle.current_status, "value", str(updated_lifecycle.current_status)),
        "rubric_decision": rubric_decision,
    }


def handle_activate_item(user_id: str, payload: dict, context: dict) -> dict:
    """
    Move item from AUTO_VALIDATED to ACTIVE status.
    
    Payload:
        - item_id: Item to activate
        - lifecycle_data: ItemLifecycle dict
    
    Returns:
        - Updated lifecycle with ACTIVE status
    """
    
    from backend.qa_engine.lifecycle import ItemLifecycle
    
    item_id = payload.get("item_id")
    lifecycle_data = payload.get("lifecycle_data")
    if item_id:
        lifecycle = get_lifecycle(item_id)
    elif lifecycle_data:
        lifecycle = ItemLifecycle(**lifecycle_data)
    else:
        return {
            "status": "error",
            "message": "item_id or lifecycle_data required",
            "user_id": user_id,
        }

    if not lifecycle:
        return {
            "status": "error",
            "message": f"Lifecycle not found for item: {item_id}",
            "user_id": user_id,
        }
    
    success, message, updated = transition_item(
        lifecycle,
        ItemStatus.ACTIVE,
        "Auto-activated: passed all QA gates",
        user_id,
    )
    
    if success:
        save_lifecycle(updated)
    
    return {
        "status": "ok" if success else "error",
        "message": message,
        "item_id": lifecycle.item_id,
        "current_status": updated.current_status.value if hasattr(updated.current_status, 'value') else str(updated.current_status),
        "lifecycle": updated.dict(),
    }


def handle_monitor_drift(user_id: str, payload: dict, context: dict) -> dict:
    """
    Monitor active item for metric drift.
    
    Payload:
        - item_id: Item to monitor
        - monitoring_data: Dict with metrics from past 30 days
    
    Returns:
        - DriftMonitoringResult
        - Recommended action (monitor, retire, investigate)
    """
    
    # TODO: Implement drift detection logic
    # For now, return stub
    
    return {
        "status": "ok",
        "message": "Drift monitoring executed (stub)",
        "item_id": payload.get("item_id"),
        "next_step": "none",
    }


def handle_retire_item(user_id: str, payload: dict, context: dict) -> dict:
    """
    Retire an item from active use.
    
    Payload:
        - item_id: Item to retire
        - reason: Retirement reason
        - lifecycle_data: ItemLifecycle dict
    
    Returns:
        - Updated lifecycle with RETIRED status
    """
    
    from backend.qa_engine.lifecycle import ItemLifecycle
    
    item_id = payload.get("item_id")
    lifecycle_data = payload.get("lifecycle_data")
    reason = payload.get("reason", "Retired by system")
    
    if item_id:
        lifecycle = get_lifecycle(item_id)
    elif lifecycle_data:
        lifecycle = ItemLifecycle(**lifecycle_data)
    else:
        return {
            "status": "error",
            "message": "item_id or lifecycle_data required",
            "user_id": user_id,
        }

    if not lifecycle:
        return {
            "status": "error",
            "message": f"Lifecycle not found for item: {item_id}",
            "user_id": user_id,
        }
    
    success, message, updated = transition_item(
        lifecycle,
        ItemStatus.RETIRED,
        reason,
        user_id,
    )
    
    if success:
        save_lifecycle(updated)
    
    return {
        "status": "ok" if success else "error",
        "message": message,
        "item_id": lifecycle.item_id,
        "current_status": updated.current_status.value if hasattr(updated.current_status, 'value') else str(updated.current_status),
    }


__all__ = [
    "run_qa_workflow",
    "handle_generate_item",
    "handle_validate_item",
    "handle_activate_item",
    "handle_monitor_drift",
    "handle_retire_item",
]
