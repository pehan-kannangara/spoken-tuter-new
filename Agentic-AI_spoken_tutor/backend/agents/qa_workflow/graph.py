"""
QA Agent Graph

LangGraph-based orchestration for QA workflows.
Integrates item generation, validation, calibration, and monitoring.
"""

from typing import Dict, Any
from datetime import datetime
import uuid

from backend.qa_engine.config import ItemStatus, ValidationGate
from backend.qa_engine.schemas import (
    QuestionItem,
    ItemSpecification,
    QAValidationReport,
)
from backend.qa_engine.orchestrator import run_qa_validation_pipeline, should_auto_activate
from backend.qa_engine.lifecycle import create_lifecycle, apply_validation_report, transition_item


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
    
    # TODO: In production, call LLM generation service here
    # For now, return stub
    
    item = QuestionItem(
        item_id=str(uuid.uuid4()),
        spec_id=spec_id,
        instruction="[Generated instruction placeholder]",
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
    
    item_data = payload.get("item_data")
    if not item_data:
        return {
            "status": "error",
            "message": "item_data required",
            "user_id": user_id,
        }
    
    # Reconstruct item from dict
    item = QuestionItem(**item_data)
    
    # TODO: In production, fetch existing_active_items from DB
    existing_items = []
    
    # Run validation pipeline
    report = run_qa_validation_pipeline(
        item=item,
        existing_active_items=existing_items,
        run_all_gates=True,
        user_id=user_id,
    )
    
    # Determine next action
    if report.overall_pass:
        next_step = "activate_item" if should_auto_activate(report) else "expert_review"
    else:
        next_step = "reject_item" if report.recommended_action == "reject" else "expert_review"
    
    return {
        "status": "ok",
        "message": f"Validation complete. Quality score: {report.quality_score:.1f}/100",
        "item_id": item.item_id,
        "report": report.dict(),
        "recommended_action": report.recommended_action,
        "next_step": next_step,
        "quality_score": report.quality_score,
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
    
    lifecycle_data = payload.get("lifecycle_data")
    if not lifecycle_data:
        return {
            "status": "error",
            "message": "lifecycle_data required",
            "user_id": user_id,
        }
    
    lifecycle = ItemLifecycle(**lifecycle_data)
    
    success, message, updated = transition_item(
        lifecycle,
        ItemStatus.ACTIVE,
        "Auto-activated: passed all QA gates",
        user_id,
    )
    
    if success:
        # TODO: In production, save updated lifecycle to DB
        # TODO: Add item to active question bank
        pass
    
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
    
    lifecycle_data = payload.get("lifecycle_data")
    reason = payload.get("reason", "Retired by system")
    
    if not lifecycle_data:
        return {
            "status": "error",
            "message": "lifecycle_data required",
            "user_id": user_id,
        }
    
    lifecycle = ItemLifecycle(**lifecycle_data)
    
    success, message, updated = transition_item(
        lifecycle,
        ItemStatus.RETIRED,
        reason,
        user_id,
    )
    
    if success:
        # TODO: In production, remove from active bank, archive
        pass
    
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
