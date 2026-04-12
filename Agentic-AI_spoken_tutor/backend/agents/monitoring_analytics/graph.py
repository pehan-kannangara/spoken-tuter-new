"""
Monitoring & Analytics Agent (Teacher Dashboard)

Handles:
  class_overview     — aggregate metrics for all learners in a class
  learner_detail     — full progress timeline + risk flags for one learner
  risk_check         — identify at-risk learners (stagnation / regression)
  create_class       — teacher registers a new class
  get_classes        — list teacher's classes
"""

from datetime import datetime, timedelta

from backend.stores.learner_store import (
    Class,
    get_class,
    get_learner,
    get_learner_sessions,
    get_progress,
    get_teacher_classes,
    create_class,
    get_all_learners,
)


# A learner is "at risk" if any of these conditions hold
_AT_RISK_NO_ACTIVITY_DAYS = 14      # no session in 14 days
_AT_RISK_REGRESSION_THRESHOLD = 0.5  # band dropped by ≥ 0.5 since last record


def run_monitoring_analytics(user_id: str, payload: dict, context: dict) -> dict:
    event_type = payload.get("event_type", "class_overview")

    if event_type == "class_overview":
        return _handle_class_overview(payload)
    elif event_type == "learner_detail":
        return _handle_learner_detail(payload)
    elif event_type == "risk_check":
        return _handle_risk_check(payload)
    elif event_type == "create_class":
        return _handle_create_class(user_id, payload)
    elif event_type == "get_classes":
        return _handle_get_classes(user_id)
    else:
        return {"status": "error", "message": f"Unknown monitoring event: {event_type}"}


def _handle_class_overview(payload: dict) -> dict:
    class_id = payload.get("class_id", "")
    cls = get_class(class_id)
    if not cls:
        return {"status": "error", "message": f"Class not found: {class_id}"}

    learners = [l for lid in cls.learner_ids if (l := get_learner(lid)) is not None]

    if not learners:
        return {
            "status": "ok",
            "class_id": class_id,
            "class_name": cls.class_name,
            "total_learners": 0,
            "avg_band": None,
            "at_risk_count": 0,
            "learner_summaries": [],
        }

    active_bands = [l.current_band for l in learners if l.current_band > 0]
    avg_band = round(sum(active_bands) / len(active_bands), 1) if active_bands else 0.0

    summaries = []
    at_risk_count = 0
    for learner in learners:
        risk_flags = _compute_risk_flags(learner.learner_id)
        is_at_risk = len(risk_flags) > 0
        if is_at_risk:
            at_risk_count += 1
        summaries.append({
            "learner_id":    learner.learner_id,
            "name":          learner.name,
            "current_band":  learner.current_band,
            "current_cefr":  learner.current_cefr,
            "last_active":   learner.last_active_at.isoformat(),
            "sessions_done": len(learner.session_ids),
            "at_risk":       is_at_risk,
            "risk_flags":    risk_flags,
        })

    # Sort: at-risk first, then by band ascending (needs improvement first)
    summaries.sort(key=lambda s: (not s["at_risk"], s["current_band"]))

    return {
        "status": "ok",
        "class_id":       class_id,
        "class_name":     cls.class_name,
        "total_learners": len(learners),
        "avg_band":       avg_band,
        "at_risk_count":  at_risk_count,
        "learner_summaries": summaries,
    }


def _handle_learner_detail(payload: dict) -> dict:
    learner_id = payload.get("learner_id", "")
    learner = get_learner(learner_id)
    if not learner:
        return {"status": "error", "message": f"Learner not found: {learner_id}"}

    records = get_progress(learner_id)
    timeline = [
        {"date": r.recorded_at.isoformat(), "band": r.band, "cefr": r.cefr}
        for r in sorted(records, key=lambda r: r.recorded_at)
    ]

    sessions = get_learner_sessions(learner_id)
    session_summaries = [
        {
            "session_id":   s.session_id,
            "type":         s.session_type,
            "status":       s.status,
            "band":         s.overall_band,
            "started":      s.started_at.isoformat(),
            "completed":    s.completed_at.isoformat() if s.completed_at else None,
        }
        for s in sorted(sessions, key=lambda s: s.started_at)
    ]

    risk_flags = _compute_risk_flags(learner_id)

    return {
        "status":        "ok",
        "learner_id":    learner_id,
        "name":          learner.name,
        "pathway":       learner.pathway,
        "current_band":  learner.current_band,
        "current_cefr":  learner.current_cefr,
        "target_band":   learner.target_band,
        "target_cefr":   learner.target_cefr,
        "streak_days":   learner.streak_days,
        "badges":        learner.badges,
        "risk_flags":    risk_flags,
        "progress_timeline": timeline,
        "session_history":   session_summaries,
    }


def _handle_risk_check(payload: dict) -> dict:
    class_id = payload.get("class_id", "")
    cls = get_class(class_id)
    if not cls:
        return {"status": "error", "message": f"Class not found: {class_id}"}

    at_risk = []
    for lid in cls.learner_ids:
        flags = _compute_risk_flags(lid)
        if flags:
            learner = get_learner(lid)
            at_risk.append({
                "learner_id": lid,
                "name":       learner.name if learner else "Unknown",
                "risk_flags": flags,
            })

    return {
        "status":         "ok",
        "class_id":       class_id,
        "at_risk_count":  len(at_risk),
        "at_risk_learners": at_risk,
    }


def _handle_create_class(teacher_id: str, payload: dict) -> dict:
    class_name = payload.get("class_name", "My Class")
    cls = create_class(teacher_id=teacher_id, class_name=class_name)
    return {
        "status":     "ok",
        "message":    f"Class '{class_name}' created.",
        "class_id":   cls.class_id,
        "class_code": cls.class_code,
        "class":      cls.model_dump(),
    }


def _handle_get_classes(teacher_id: str) -> dict:
    classes = get_teacher_classes(teacher_id)
    return {
        "status": "ok",
        "count":  len(classes),
        "classes": [c.model_dump() for c in classes],
    }


# ---------------------------------------------------------------------------
# Risk detection helpers
# ---------------------------------------------------------------------------

def _compute_risk_flags(learner_id: str) -> list[str]:
    flags: list[str] = []
    learner = get_learner(learner_id)
    if not learner:
        return flags

    # 1. No activity in N days
    days_inactive = (datetime.utcnow() - learner.last_active_at).days
    if days_inactive >= _AT_RISK_NO_ACTIVITY_DAYS:
        flags.append(f"No activity for {days_inactive} days")

    # 2. Band regression (last two progress records)
    records = sorted(get_progress(learner_id), key=lambda r: r.recorded_at)
    if len(records) >= 2:
        latest_band = records[-1].band
        prev_band   = records[-2].band
        drop = prev_band - latest_band
        if drop >= _AT_RISK_REGRESSION_THRESHOLD:
            flags.append(f"Band regression: {prev_band} → {latest_band} (−{drop:.1f})")

    # 3. Zero sessions after registration (more than 3 days old, never practised)
    days_since_join = (datetime.utcnow() - learner.created_at).days
    if days_since_join >= 3 and len(learner.session_ids) == 0:
        flags.append("Never started a session since registration")

    return flags
