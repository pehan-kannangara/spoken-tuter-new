"""
Recruiter Screening Agent

Handles:
  create_screening_pack   — define a role screening profile + question set
  add_candidate           — register a candidate against a pack
  start_candidate_session — create a screening session for a candidate
  get_pack_results        — aggregate all candidate results for a pack
  get_pack                — retrieve pack details
"""

import random

from backend.stores.learner_store import (
    ScreeningPack,
    create_screening_pack,
    create_session,
    get_screening_pack,
    get_session,
    get_recruiter_packs,
    add_candidate_to_pack,
    record_screening_session,
    cefr_to_min_band,
)
from backend.qa_engine.store import list_active_items


BUSINESS_TASK_TYPES_BY_LEVEL = {
    "junior": {"business_meeting_intro", "business_status_update", "business_client_call"},
    "mid": {"business_status_update", "business_client_call", "business_presentation", "business_negotiation"},
    "senior": {"business_presentation", "business_negotiation", "business_leadership_pitch", "business_executive_update"},
    "executive": {"business_presentation", "business_leadership_pitch", "business_executive_update"},
}


def _resolve_thresholds(payload: dict, min_band: float, min_cefr: str) -> tuple[float, str]:
    payload_min_cefr = str(payload.get("min_cefr") or min_cefr).lower()
    payload_min_band = payload.get("min_band")
    if payload_min_band is None and payload_min_cefr:
        payload_min_band = cefr_to_min_band(payload_min_cefr)
    resolved_band = float(payload_min_band if payload_min_band is not None else min_band)
    resolved_cefr = payload_min_cefr or min_cefr
    return resolved_band, resolved_cefr


def _select_screening_questions(pack: ScreeningPack, payload: dict, context: dict) -> list[str]:
    all_active = list_active_items()
    if not all_active:
        return []

    screening_pathway = str(
        payload.get("screening_pathway")
        or context.get("actor", {}).get("pathway")
        or "business_english"
    ).lower()
    preferred_domains = payload.get("preferred_domains") or context.get("screening_policy", {}).get("preferred_domains") or ["business"]
    preferred_domains = [str(domain).lower() for domain in preferred_domains]

    min_band, min_cefr = _resolve_thresholds(payload, pack.min_band, pack.min_cefr)
    _ = min_cefr

    job_level = str(payload.get("job_level") or pack.job_level or "mid").lower()
    business_task_types = BUSINESS_TASK_TYPES_BY_LEVEL.get(job_level, BUSINESS_TASK_TYPES_BY_LEVEL["mid"])

    pathway_filtered = [
        item for item in all_active
        if str(item.pathway).lower() == screening_pathway
    ]
    if not pathway_filtered:
        pathway_filtered = all_active

    def is_eligible(item) -> bool:
        try:
            target_band = cefr_to_min_band(str(item.target_level))
        except Exception:
            target_band = min_band
        return target_band >= max(min_band - 0.5, 1.0)

    domain_filtered = [
        item for item in pathway_filtered
        if str(item.domain).lower() in preferred_domains and is_eligible(item)
    ]

    if screening_pathway == "business_english":
        business_first = [
            item for item in domain_filtered
            if str(item.task_type) in business_task_types
        ]
        if len(business_first) >= pack.questions_per_candidate:
            candidates_qs = business_first
        else:
            candidates_qs = business_first + [item for item in domain_filtered if item not in business_first]
    else:
        candidates_qs = domain_filtered

    if len(candidates_qs) < pack.questions_per_candidate:
        candidates_qs = [item for item in pathway_filtered if is_eligible(item)]
    if len(candidates_qs) < pack.questions_per_candidate:
        candidates_qs = pathway_filtered

    selected = random.sample(candidates_qs, min(pack.questions_per_candidate, len(candidates_qs)))
    return [q.item_id for q in selected]


def run_recruiter_screening(user_id: str, payload: dict, context: dict) -> dict:
    event_type = payload.get("event_type", "get_pack")

    if event_type == "create_screening_pack":
        return _handle_create_pack(user_id, payload, context)
    elif event_type == "add_candidate":
        return _handle_add_candidate(payload)
    elif event_type == "start_candidate_session":
        return _handle_start_session(payload, context)
    elif event_type == "get_pack_results":
        return _handle_get_results(payload)
    elif event_type == "get_pack":
        return _handle_get_pack(payload)
    elif event_type == "list_packs":
        return _handle_list_packs(user_id)
    else:
        return {"status": "error", "message": f"Unknown recruiter event: {event_type}"}


def _handle_create_pack(recruiter_id: str, payload: dict, context: dict) -> dict:
    role_name   = payload.get("role_name", "General Role")
    department  = payload.get("department", "Operations")
    job_level   = payload.get("job_level", "mid")
    requested_cefr = str(payload.get("min_cefr") or "b2").lower()
    min_band    = float(payload.get("min_band", cefr_to_min_band(requested_cefr)))
    min_cefr    = requested_cefr
    q_count     = int(payload.get("questions_per_candidate", 5))
    screening_pathway = str(
        payload.get("screening_pathway")
        or context.get("actor", {}).get("pathway")
        or "business_english"
    ).lower()

    pack = create_screening_pack(
        recruiter_id=recruiter_id,
        role_name=role_name,
        department=department,
        job_level=job_level,
        min_band=min_band,
        min_cefr=min_cefr,
        questions_per_candidate=q_count,
    )

    return {
        "status": "ok",
        "message": f"Screening pack created for role: {role_name}",
        "pack_id": pack.pack_id,
        "screening_pathway": screening_pathway,
        "pack": pack.model_dump(),
    }


def _handle_add_candidate(payload: dict) -> dict:
    pack_id    = payload.get("pack_id", "")
    learner_id = payload.get("learner_id", "")

    if not pack_id or not learner_id:
        return {"status": "error", "message": "pack_id and learner_id required."}

    success = add_candidate_to_pack(pack_id, learner_id)
    if not success:
        return {"status": "error", "message": f"Pack not found: {pack_id}"}

    return {
        "status": "ok",
        "message": f"Candidate {learner_id} added to pack {pack_id}",
    }


def _handle_start_session(payload: dict, context: dict) -> dict:
    pack_id    = payload.get("pack_id", "")
    learner_id = payload.get("learner_id", "")

    pack = get_screening_pack(pack_id)
    if not pack:
        return {"status": "error", "message": f"Pack not found: {pack_id}"}

    question_ids = _select_screening_questions(pack, payload, context)
    if not question_ids:
        return {"status": "error", "message": "No active questions available for screening."}

    screening_pathway = str(
        payload.get("screening_pathway")
        or context.get("actor", {}).get("pathway")
        or "business_english"
    ).lower()

    session = create_session(
        learner_id=learner_id,
        pathway=screening_pathway,
        session_type="recruiter_screening",
        question_ids=question_ids,
    )
    record_screening_session(pack_id, session.session_id)

    return {
        "status": "ok",
        "message": "Screening session started.",
        "session_id": session.session_id,
        "pack_id": pack_id,
        "screening_pathway": screening_pathway,
        "questions": [
            {"index": i, "item_id": qid}
            for i, qid in enumerate(question_ids)
        ],
    }


def _handle_get_results(payload: dict) -> dict:
    pack_id = payload.get("pack_id", "")
    pack = get_screening_pack(pack_id)
    if not pack:
        return {"status": "error", "message": f"Pack not found: {pack_id}"}

    results = []
    for session_id in pack.completed_session_ids:
        session = get_session(session_id)
        if not session:
            continue
        passed = (
            session.overall_band is not None
            and session.overall_band >= pack.min_band
        )
        results.append({
            "learner_id":   session.learner_id,
            "session_id":   session_id,
            "overall_band": session.overall_band,
            "overall_cefr": session.overall_cefr,
            "status":       session.status,
            "passed_threshold": passed,
        })

    total = len(results)
    passed_count = sum(1 for r in results if r["passed_threshold"])

    return {
        "status": "ok",
        "pack_id": pack_id,
        "role_name": pack.role_name,
        "min_band_required": pack.min_band,
        "candidates_screened": total,
        "candidates_passed": passed_count,
        "pass_rate": round(passed_count / total * 100, 1) if total else 0.0,
        "results": results,
    }


def _handle_get_pack(payload: dict) -> dict:
    pack_id = payload.get("pack_id", "")
    pack = get_screening_pack(pack_id)
    if not pack:
        return {"status": "error", "message": f"Pack not found: {pack_id}"}
    return {"status": "ok", "pack": pack.model_dump()}


def _handle_list_packs(recruiter_id: str) -> dict:
    packs = get_recruiter_packs(recruiter_id)
    return {
        "status": "ok",
        "count": len(packs),
        "packs": [p.model_dump() for p in packs],
    }
