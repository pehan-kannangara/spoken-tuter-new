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


def run_recruiter_screening(user_id: str, payload: dict, context: dict) -> dict:
    event_type = payload.get("event_type", "get_pack")

    if event_type == "create_screening_pack":
        return _handle_create_pack(user_id, payload)
    elif event_type == "add_candidate":
        return _handle_add_candidate(payload)
    elif event_type == "start_candidate_session":
        return _handle_start_session(payload)
    elif event_type == "get_pack_results":
        return _handle_get_results(payload)
    elif event_type == "get_pack":
        return _handle_get_pack(payload)
    elif event_type == "list_packs":
        return _handle_list_packs(user_id)
    else:
        return {"status": "error", "message": f"Unknown recruiter event: {event_type}"}


def _handle_create_pack(recruiter_id: str, payload: dict) -> dict:
    role_name   = payload.get("role_name", "General Role")
    department  = payload.get("department", "Operations")
    job_level   = payload.get("job_level", "mid")
    min_band    = float(payload.get("min_band", 6.0))
    min_cefr    = payload.get("min_cefr", "b2")
    q_count     = int(payload.get("questions_per_candidate", 5))

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


def _handle_start_session(payload: dict) -> dict:
    pack_id    = payload.get("pack_id", "")
    learner_id = payload.get("learner_id", "")

    pack = get_screening_pack(pack_id)
    if not pack:
        return {"status": "error", "message": f"Pack not found: {pack_id}"}

    # Select questions from active bank at appropriate level
    all_active = list_active_items()
    min_band = pack.min_band

    # Filter by pathway agnostic — pick questions at B2/C1 for professional screening
    candidates_qs = [
        item for item in all_active
        if item.task_type in ("part_1", "part_2", "part_3", "cefr_upper_intermediate")
    ]

    if len(candidates_qs) < pack.questions_per_candidate:
        candidates_qs = all_active  # fallback: use any active item

    selected = random.sample(
        candidates_qs,
        min(pack.questions_per_candidate, len(candidates_qs)),
    )
    question_ids = [q.item_id for q in selected]

    session = create_session(
        learner_id=learner_id,
        pathway="ielts",
        session_type="recruiter_screening",
        question_ids=question_ids,
    )
    record_screening_session(pack_id, session.session_id)

    return {
        "status": "ok",
        "message": "Screening session started.",
        "session_id": session.session_id,
        "pack_id": pack_id,
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
