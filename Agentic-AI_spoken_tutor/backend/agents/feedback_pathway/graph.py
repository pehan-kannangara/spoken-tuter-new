"""
Feedback Pathway Agent

Handles:
  get_feedback      — return stored feedback for a session/question
  get_progress      — summarise learner progress timeline
  get_pathway       — recommend next study activities based on weak areas
"""

from backend.stores.learner_store import (
    get_learner,
    get_progress,
    get_session,
    band_to_cefr,
)


# CEFR level order for progress delta computation
_CEFR_ORDER = ["a1", "a2", "b1", "b2", "c1", "c2"]

# Activity recommendations keyed by (criterion, cefr_level)
_ACTIVITIES: dict[str, dict[str, list[str]]] = {
    "Fluency & Coherence": {
        "a1": ["Daily 1-minute monologue on simple topics (home, family, food)"],
        "a2": ["2-minute storytelling using past tense", "Read short texts aloud for 10 min/day"],
        "b1": ["IELTS Part 1 timed practice (1 min per question)", "Listen and shadow BBC 6-minute English"],
        "b2": ["IELTS Part 2 2-minute cue card sets", "Record and self-review for pauses"],
        "c1": ["IELTS Part 3 discussion sets", "Debate structured arguments without notes"],
    },
    "Lexical Resource": {
        "a1": ["Learn 5 core topic words/day (family, colours, numbers)"],
        "a2": ["Build topic word lists: travel, food, hobbies", "Anki flashcard daily review"],
        "b1": ["Learn collocations from English in Use (Cambridge)", "Word family practice sets"],
        "b2": ["Advanced Academic Wordlist (AWL) exercises", "Read The Guardian / BBC News weekly"],
        "c1": ["Native-level idiomatic expressions", "TED Talk vocabulary extraction"],
    },
    "Grammatical Range": {
        "a1": ["Present simple + 'to be' drills", "Short sentence writing practice"],
        "a2": ["Past simple storytelling tasks", "Conjunction practice: and, but, because, so"],
        "b1": ["Relative clause insertion exercises", "Conditional sentences (1st and 2nd)"],
        "b2": ["Complex sentence transformation tasks", "Passive voice practice in speaking"],
        "c1": ["Advanced clause complexity", "Nominal/cleft sentence practice"],
    },
}


def run_feedback_pathway(user_id: str, payload: dict, context: dict) -> dict:
    event_type = payload.get("event_type", "get_feedback")

    if event_type == "get_feedback":
        return _handle_get_feedback(payload)
    elif event_type == "get_progress":
        return _handle_get_progress(payload)
    elif event_type == "get_pathway":
        return _handle_get_pathway(payload)
    else:
        return {"status": "error", "message": f"Unknown feedback event: {event_type}"}


def _handle_get_feedback(payload: dict) -> dict:
    session_id     = payload.get("session_id", "")
    question_index = payload.get("question_index")

    session = get_session(session_id)
    if not session:
        return {"status": "error", "message": f"Session not found: {session_id}"}

    if question_index is not None:
        score = session.scores.get(int(question_index))
        if not score:
            return {"status": "error", "message": "No score found for that question index."}
        return {"status": "ok", "score": score.model_dump()}

    # Return all scores for the session
    return {
        "status": "ok",
        "session_id": session_id,
        "scores": {str(k): v.model_dump() for k, v in session.scores.items()},
        "overall_band": session.overall_band,
        "overall_cefr": session.overall_cefr,
    }


def _handle_get_progress(payload: dict) -> dict:
    learner_id = payload.get("learner_id", "")
    learner = get_learner(learner_id)
    if not learner:
        return {"status": "error", "message": f"Learner not found: {learner_id}"}

    records = get_progress(learner_id)
    timeline = [
        {
            "date": r.recorded_at.isoformat(),
            "band": r.band,
            "cefr": r.cefr,
            "session_id": r.session_id,
        }
        for r in sorted(records, key=lambda r: r.recorded_at)
    ]

    # Band delta (first vs latest)
    delta_band = 0.0
    if len(timeline) >= 2:
        delta_band = round(timeline[-1]["band"] - timeline[0]["band"], 1)

    return {
        "status": "ok",
        "learner_id": learner_id,
        "current_band": learner.current_band,
        "current_cefr": learner.current_cefr,
        "target_band": learner.target_band,
        "target_cefr": learner.target_cefr,
        "sessions_completed": len(timeline),
        "band_improvement": delta_band,
        "timeline": timeline,
    }


def _handle_get_pathway(payload: dict) -> dict:
    learner_id = payload.get("learner_id", "")
    weak_criterion = payload.get("weak_criterion", "Fluency & Coherence")

    learner = get_learner(learner_id)
    if not learner:
        return {"status": "error", "message": f"Learner not found: {learner_id}"}

    cefr = learner.current_cefr.lower() if learner.current_cefr else "b1"
    criterion_activities = _ACTIVITIES.get(weak_criterion, {})
    activities = criterion_activities.get(cefr, ["Continue regular timed speaking practice."])

    # Next target level
    current_idx = _CEFR_ORDER.index(cefr) if cefr in _CEFR_ORDER else 2
    next_level  = _CEFR_ORDER[min(current_idx + 1, len(_CEFR_ORDER) - 1)]

    return {
        "status": "ok",
        "learner_id": learner_id,
        "current_level": cefr.upper(),
        "target_level": next_level.upper(),
        "focus_criterion": weak_criterion,
        "recommended_activities": activities,
        "sessions_to_next_level_estimate": max(4, (6 - current_idx) * 3),
    }
