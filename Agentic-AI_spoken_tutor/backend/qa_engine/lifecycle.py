"""
Item Lifecycle Manager

Manages state transitions for question items and maintains full audit trail.
Ensures only valid transitions occur and logs all changes.
"""

import uuid
from datetime import datetime
from typing import Optional

from backend.qa_engine.config import ItemStatus, AUTO_PUBLISH
from backend.qa_engine.schemas import (
    ItemLifecycle,
    ItemEventLog,
    QAValidationReport,
    QuestionItem,
)


# Valid state transitions
VALID_TRANSITIONS = {
    ItemStatus.DRAFT: [ItemStatus.AUTO_VALIDATED, ItemStatus.REJECTED],
    ItemStatus.AUTO_VALIDATED: [ItemStatus.EXPERT_REVIEW_PENDING, ItemStatus.EXPERT_APPROVED, ItemStatus.REJECTED],
    ItemStatus.EXPERT_REVIEW_PENDING: [ItemStatus.EXPERT_APPROVED, ItemStatus.REJECTED],
    ItemStatus.EXPERT_APPROVED: [ItemStatus.SHADOW_TESTING, ItemStatus.REJECTED],
    ItemStatus.SHADOW_TESTING: [ItemStatus.SHADOW_CALIBRATED, ItemStatus.REJECTED],
    ItemStatus.SHADOW_CALIBRATED: [ItemStatus.ACTIVE, ItemStatus.REJECTED],
    ItemStatus.ACTIVE: [ItemStatus.MONITORING, ItemStatus.DRIFT_FLAGGED, ItemStatus.RETIRED],
    ItemStatus.MONITORING: [ItemStatus.ACTIVE, ItemStatus.DRIFT_FLAGGED, ItemStatus.RETIRED],
    ItemStatus.DRIFT_FLAGGED: [ItemStatus.ACTIVE, ItemStatus.RETIRED],
    ItemStatus.RETIRED: [],  # Terminal state
    ItemStatus.REJECTED: [],  # Terminal state
}


def create_lifecycle(item: QuestionItem, created_by: str) -> ItemLifecycle:
    """Initialize a new item lifecycle record."""
    
    lifecycle = ItemLifecycle(
        item_id=item.item_id,
        current_status=ItemStatus.DRAFT,
        created_at=datetime.utcnow(),
        first_activated_at=None,
        retired_at=None,
        events=[],
        spec_id=item.spec_id,
        pathway=item.pathway,
        target_level=item.target_level,
    )
    
    # Log creation event
    creation_event = ItemEventLog(
        event_id=str(uuid.uuid4()),
        item_id=item.item_id,
        event_type="created",
        from_status=ItemStatus.DRAFT,
        to_status=ItemStatus.DRAFT,
        reason="Item generated",
        triggered_by=created_by,
        timestamp=datetime.utcnow(),
    )
    
    lifecycle.events.append(creation_event)
    
    return lifecycle


def transition_item(
    lifecycle: ItemLifecycle,
    to_status: ItemStatus,
    reason: str,
    triggered_by: str,
    decision_data: Optional[dict] = None,
) -> tuple[bool, str, ItemLifecycle]:
    """
    Attempt to transition item to new status.
    
    Returns:
        (success: bool, message: str, updated_lifecycle: ItemLifecycle)
    """
    
    current_status = lifecycle.current_status
    
    # Check if transition is valid
    valid_targets = VALID_TRANSITIONS.get(current_status, [])
    if to_status not in valid_targets:
        return (
            False,
            f"Invalid transition: {current_status} -> {to_status}. Valid targets: {valid_targets}",
            lifecycle,
        )
    
    # Create event log
    event = ItemEventLog(
        event_id=str(uuid.uuid4()),
        item_id=lifecycle.item_id,
        event_type="transitioned",
        from_status=current_status,
        to_status=to_status,
        reason=reason,
        triggered_by=triggered_by,
        decision_data=decision_data or {},
        timestamp=datetime.utcnow(),
    )
    
    # Update lifecycle
    lifecycle.events.append(event)
    lifecycle.current_status = to_status
    
    # Mark first activation
    if to_status == ItemStatus.ACTIVE and lifecycle.first_activated_at is None:
        lifecycle.first_activated_at = datetime.utcnow()
    
    # Mark retirement
    if to_status == ItemStatus.RETIRED and lifecycle.retired_at is None:
        lifecycle.retired_at = datetime.utcnow()
    
    return (
        True,
        f"Transitioned {lifecycle.item_id} from {current_status} to {to_status}",
        lifecycle,
    )


def apply_validation_report(
    lifecycle: ItemLifecycle,
    report: QAValidationReport,
    user_id: str = "system",
) -> tuple[bool, str, ItemLifecycle]:
    """
    Apply validation report to item lifecycle.
    Automatically advances item if it passes required gates.
    """
    
    if report.overall_pass:
        # Move to next stage based on recommendation
        next_stage = report.next_stage_if_accepted
        if next_stage:
            reason = f"Validation passed with quality score {report.quality_score:.1f}/100"
            return transition_item(
                lifecycle,
                next_stage,
                reason,
                user_id,
                decision_data={"quality_score": report.quality_score, "report_id": report.report_id},
            )
    else:
        # Validation failed
        if report.recommended_action == "reject":
            reason = f"Validation rejected: {'; '.join(report.critical_issues[:3])}"
            return transition_item(
                lifecycle,
                ItemStatus.REJECTED,
                reason,
                user_id,
                decision_data={"report_id": report.report_id, "issues": report.critical_issues},
            )
        elif report.recommended_action == "review":
            # Move to expert review
            reason = f"Requires expert review. Quality score: {report.quality_score:.1f}/100"
            return transition_item(
                lifecycle,
                ItemStatus.EXPERT_REVIEW_PENDING,
                reason,
                user_id,
                decision_data={
                    "report_id": report.report_id,
                    "warnings": report.warnings,
                    "quality_score": report.quality_score,
                },
            )
    
    return (False, "No valid transition determined from validation report", lifecycle)


def get_event_history(lifecycle: ItemLifecycle) -> list[dict]:
    """Return audit trail as human-readable records."""
    
    history = []
    for event in lifecycle.events:
        history.append({
            "timestamp": event.timestamp.isoformat(),
            "event_type": event.event_type,
            "from_status": event.from_status.value if event.from_status else None,
            "to_status": event.to_status.value if event.to_status else None,
            "reason": event.reason,
            "triggered_by": event.triggered_by,
        })
    
    return history


def get_active_duration_days(lifecycle: ItemLifecycle) -> Optional[int]:
    """Calculate days from first activation to retirement/current."""
    
    if lifecycle.first_activated_at is None:
        return None
    
    end_date = lifecycle.retired_at or datetime.utcnow()
    return (end_date - lifecycle.first_activated_at).days


__all__ = [
    "create_lifecycle",
    "transition_item",
    "apply_validation_report",
    "get_event_history",
    "get_active_duration_days",
    "VALID_TRANSITIONS",
]
