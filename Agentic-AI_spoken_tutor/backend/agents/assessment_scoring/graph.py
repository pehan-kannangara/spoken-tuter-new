"""
Assessment Scoring Agent

Handles two event types:
  submit_response  — score a single learner response and save to store
  score_session    — (re)compute overall band from all scored responses

Scoring is deterministic (no LLM) — fully auditable.
"""

import uuid
from datetime import datetime

from backend.agents.assessment_scoring.scorer import score_response
from backend.agents.feedback_pathway.feedback_generator import generate_feedback
from backend.stores.learner_store import (
    AssessmentScore,
    SubmittedResponse,
    get_session,
    save_response,
    save_score,
)


def run_assessment_scoring(user_id: str, payload: dict, context: dict) -> dict:
    event_type = payload.get("event_type", "submit_response")

    if event_type == "submit_response":
        return _handle_submit_response(user_id, payload)
    elif event_type == "score_session":
        return _handle_score_session(user_id, payload)
    else:
        return {
            "status": "error",
            "message": f"Unknown assessment event: {event_type}",
        }


def _handle_submit_response(user_id: str, payload: dict) -> dict:
    """
    Score a single transcript and store the result.

    Required payload keys:
      session_id, item_id, question_index, transcript, task_type
    """
    session_id     = payload.get("session_id", "")
    item_id        = payload.get("item_id", "")
    question_index = int(payload.get("question_index", 0))
    transcript     = payload.get("transcript", "")
    task_type      = payload.get("task_type", "part_1")

    if not transcript.strip():
        return {"status": "error", "message": "Transcript is empty."}

    # 1. Score
    result = score_response(transcript, task_type)

    # 2. Generate feedback
    feedback = generate_feedback(result)

    # 3. Persist response
    response = SubmittedResponse(
        response_id=str(uuid.uuid4()),
        session_id=session_id,
        item_id=item_id,
        question_index=question_index,
        transcript=transcript,
    )
    save_response(response)

    # 4. Persist score
    score = AssessmentScore(
        score_id=str(uuid.uuid4()),
        session_id=session_id,
        item_id=item_id,
        question_index=question_index,
        fluency_coherence=result.fluency_coherence,
        lexical_resource=result.lexical_resource,
        grammatical_range=result.grammatical_range,
        overall_band=result.overall_band,
        cefr_level=result.cefr_level,
        fc_feedback=feedback.fc_description,
        lr_feedback=feedback.lr_description,
        gr_feedback=feedback.gr_description,
        overall_feedback=feedback.overall_description,
        improvement_tips=feedback.fc_tips[:2] + feedback.lr_tips[:1],
    )
    save_score(score)

    return {
        "status": "ok",
        "message": "Response scored successfully.",
        "score": {
            "fluency_coherence": result.fluency_coherence,
            "lexical_resource":  result.lexical_resource,
            "grammatical_range": result.grammatical_range,
            "overall_band":      result.overall_band,
            "cefr_level":        result.cefr_level,
        },
        "feedback": {
            "band_label":         feedback.band_label,
            "cefr_label":         feedback.cefr_label,
            "overall":            feedback.overall_description,
            "fc":                 feedback.fc_description,
            "lr":                 feedback.lr_description,
            "gr":                 feedback.gr_description,
            "encouragement":      feedback.encouragement,
            "next_focus":         feedback.next_focus,
            "improvement_tips":   feedback.fc_tips[:2] + feedback.lr_tips[:1],
        },
        "diagnostics": {
            "word_count":           result.word_count,
            "sentence_count":       result.sentence_count,
            "discourse_markers":    result.discourse_markers_found,
            "ttr":                  result.ttr,
            "avg_sentence_length":  result.avg_sentence_length,
        },
    }


def _handle_score_session(user_id: str, payload: dict) -> dict:
    session_id = payload.get("session_id", "")
    session = get_session(session_id)
    if not session:
        return {"status": "error", "message": f"Session not found: {session_id}"}

    if not session.scores:
        return {"status": "error", "message": "No responses scored yet."}

    bands = [s.overall_band for s in session.scores.values()]
    overall = round(sum(bands) / len(bands) * 2) / 2

    return {
        "status": "ok",
        "session_id": session_id,
        "overall_band": overall,
        "overall_cefr": session.overall_cefr,
        "questions_scored": len(bands),
    }
