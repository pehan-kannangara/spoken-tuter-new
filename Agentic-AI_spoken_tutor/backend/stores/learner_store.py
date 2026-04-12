"""
Learner Store

Thread-safe in-memory persistence for:
  - LearnerProfile   (registration info + current level)
  - PracticeSession  (question delivery, responses, scores)
  - ProgressRecord   (timestamped band / CEFR snapshots)
  - Class            (teacher → learner grouping)
  - ScreeningPack    (recruiter → candidate screening)

Swap the backing dicts for PostgreSQL tables in production.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from threading import Lock
from typing import Optional

from pydantic import BaseModel, Field


# ============================================================================
# DATA MODELS
# ============================================================================

class LearnerProfile(BaseModel):
    learner_id: str
    name: str
    email: str
    role: str                       # school_student | university_student | working_professional
    pathway: str                    # ielts | cefr
    goal: str                       # ielts_exam | general_improvement | for_school | working_purpose | interview_preparation
    current_band: float = 0.0       # IELTS band (1–9); 0 = not yet assessed
    current_cefr: str = "unknown"   # a1 | a2 | b1 | b2 | c1 | c2
    target_band: Optional[float] = None
    target_cefr: Optional[str] = None
    class_id: Optional[str] = None  # populated if joined via class code
    session_ids: list[str] = Field(default_factory=list)
    streak_days: int = 0
    badges: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_active_at: datetime = Field(default_factory=datetime.utcnow)


class SubmittedResponse(BaseModel):
    response_id: str
    session_id: str
    item_id: str
    question_index: int
    transcript: str                 # text transcript of the spoken response
    submitted_at: datetime = Field(default_factory=datetime.utcnow)


class AssessmentScore(BaseModel):
    score_id: str
    session_id: str
    item_id: str
    question_index: int
    # IELTS criteria (1.0–9.0, rounded to nearest 0.5)
    fluency_coherence: float
    lexical_resource: float
    grammatical_range: float
    # Computed
    overall_band: float
    cefr_level: str
    # Structured feedback per criterion
    fc_feedback: str = ""
    lr_feedback: str = ""
    gr_feedback: str = ""
    overall_feedback: str = ""
    improvement_tips: list[str] = Field(default_factory=list)
    scored_at: datetime = Field(default_factory=datetime.utcnow)


class PracticeSession(BaseModel):
    session_id: str
    learner_id: str
    pathway: str                    # ielts | cefr
    session_type: str               # practice | formal_assessment | recruiter_screening
    status: str = "active"          # active | completed | abandoned
    question_ids: list[str] = Field(default_factory=list)   # ordered item_ids
    current_index: int = 0
    responses: dict[int, SubmittedResponse] = Field(default_factory=dict)
    scores: dict[int, AssessmentScore] = Field(default_factory=dict)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    overall_band: Optional[float] = None
    overall_cefr: Optional[str] = None
    band_before_session: Optional[float] = None   # for progress delta calculation


class ProgressRecord(BaseModel):
    record_id: str
    learner_id: str
    session_id: str
    band: float
    cefr: str
    recorded_at: datetime = Field(default_factory=datetime.utcnow)


class Class(BaseModel):
    class_id: str
    teacher_id: str
    class_name: str
    class_code: str                     # 6-char alphanumeric join code
    learner_ids: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ScreeningPack(BaseModel):
    pack_id: str
    recruiter_id: str
    role_name: str
    department: str
    job_level: str                      # junior | mid | senior | executive
    min_band: float                     # minimum acceptable IELTS overall band
    min_cefr: str                       # minimum acceptable CEFR level
    questions_per_candidate: int = 5
    candidate_ids: list[str] = Field(default_factory=list)
    completed_session_ids: list[str] = Field(default_factory=list)
    status: str = "active"              # active | closed
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# THREAD-SAFE IN-MEMORY STORES
# ============================================================================

_LEARNERS:  dict[str, LearnerProfile]  = {}
_SESSIONS:  dict[str, PracticeSession] = {}
_RESPONSES: dict[str, SubmittedResponse] = {}
_SCORES:    dict[str, AssessmentScore]  = {}
_PROGRESS:  dict[str, list[ProgressRecord]] = {}   # learner_id → records
_CLASSES:   dict[str, Class]            = {}
_CLASS_CODES: dict[str, str]            = {}        # code → class_id
_PACKS:     dict[str, ScreeningPack]    = {}

_L = Lock()


# ============================================================================
# LEARNER OPERATIONS
# ============================================================================

def create_learner(
    name: str,
    email: str,
    role: str,
    pathway: str,
    goal: str,
    target_band: Optional[float] = None,
    target_cefr: Optional[str] = None,
    class_code: Optional[str] = None,
) -> LearnerProfile:
    with _L:
        learner_id = str(uuid.uuid4())
        class_id = _CLASS_CODES.get(class_code) if class_code else None
        profile = LearnerProfile(
            learner_id=learner_id,
            name=name,
            email=email,
            role=role,
            pathway=pathway,
            goal=goal,
            target_band=target_band,
            target_cefr=target_cefr,
            class_id=class_id,
        )
        _LEARNERS[learner_id] = profile
        if class_id and class_id in _CLASSES:
            _CLASSES[class_id].learner_ids.append(learner_id)
        return profile


def get_learner(learner_id: str) -> Optional[LearnerProfile]:
    with _L:
        return _LEARNERS.get(learner_id)


def update_learner_level(learner_id: str, band: float, cefr: str) -> bool:
    with _L:
        profile = _LEARNERS.get(learner_id)
        if not profile:
            return False
        profile.current_band = band
        profile.current_cefr = cefr
        profile.last_active_at = datetime.utcnow()
        return True


def get_all_learners() -> list[LearnerProfile]:
    with _L:
        return list(_LEARNERS.values())


# ============================================================================
# SESSION OPERATIONS
# ============================================================================

def create_session(
    learner_id: str,
    pathway: str,
    session_type: str,
    question_ids: list[str],
    band_before: Optional[float] = None,
) -> PracticeSession:
    with _L:
        session_id = str(uuid.uuid4())
        session = PracticeSession(
            session_id=session_id,
            learner_id=learner_id,
            pathway=pathway,
            session_type=session_type,
            question_ids=question_ids,
            band_before_session=band_before,
        )
        _SESSIONS[session_id] = session
        learner = _LEARNERS.get(learner_id)
        if learner:
            learner.session_ids.append(session_id)
            learner.last_active_at = datetime.utcnow()
        return session


def get_session(session_id: str) -> Optional[PracticeSession]:
    with _L:
        return _SESSIONS.get(session_id)


def advance_session(session_id: str) -> Optional[PracticeSession]:
    """Move to next question; mark completed when all questions answered."""
    with _L:
        session = _SESSIONS.get(session_id)
        if not session or session.status != "active":
            return session
        session.current_index += 1
        if session.current_index >= len(session.question_ids):
            _complete_session(session)
        return session


def save_response(response: SubmittedResponse) -> None:
    with _L:
        _RESPONSES[response.response_id] = response
        session = _SESSIONS.get(response.session_id)
        if session:
            session.responses[response.question_index] = response


def save_score(score: AssessmentScore) -> None:
    with _L:
        _SCORES[score.score_id] = score
        session = _SESSIONS.get(score.session_id)
        if session:
            session.scores[score.question_index] = score
            # If all questions scored, compute overall
            if len(session.scores) >= len(session.question_ids):
                bands = [s.overall_band for s in session.scores.values()]
                avg = round(sum(bands) / len(bands) * 2) / 2  # round to 0.5
                session.overall_band = avg
                session.overall_cefr = band_to_cefr(avg)
                if session.status == "active":
                    _complete_session(session)


def _complete_session(session: PracticeSession) -> None:
    """Internal: mark session done and record progress (must be called under lock)."""
    session.status = "completed"
    session.completed_at = datetime.utcnow()
    if session.overall_band:
        record = ProgressRecord(
            record_id=str(uuid.uuid4()),
            learner_id=session.learner_id,
            session_id=session.session_id,
            band=session.overall_band,
            cefr=session.overall_cefr or "unknown",
        )
        _PROGRESS.setdefault(session.learner_id, []).append(record)
        learner = _LEARNERS.get(session.learner_id)
        if learner:
            learner.current_band = session.overall_band
            learner.current_cefr = session.overall_cefr or learner.current_cefr


def get_learner_sessions(learner_id: str) -> list[PracticeSession]:
    with _L:
        return [s for s in _SESSIONS.values() if s.learner_id == learner_id]


# ============================================================================
# PROGRESS OPERATIONS
# ============================================================================

def get_progress(learner_id: str) -> list[ProgressRecord]:
    with _L:
        return list(_PROGRESS.get(learner_id, []))


# ============================================================================
# CLASS OPERATIONS
# ============================================================================

def create_class(teacher_id: str, class_name: str) -> Class:
    with _L:
        class_id = str(uuid.uuid4())
        code = _generate_class_code(class_id)
        cls = Class(
            class_id=class_id,
            teacher_id=teacher_id,
            class_name=class_name,
            class_code=code,
        )
        _CLASSES[class_id] = cls
        _CLASS_CODES[code] = class_id
        return cls


def get_class(class_id: str) -> Optional[Class]:
    with _L:
        return _CLASSES.get(class_id)


def get_teacher_classes(teacher_id: str) -> list[Class]:
    with _L:
        return [c for c in _CLASSES.values() if c.teacher_id == teacher_id]


def _generate_class_code(seed: str) -> str:
    import hashlib
    return hashlib.md5(seed.encode()).hexdigest()[:6].upper()


# ============================================================================
# SCREENING PACK OPERATIONS
# ============================================================================

def create_screening_pack(
    recruiter_id: str,
    role_name: str,
    department: str,
    job_level: str,
    min_band: float,
    min_cefr: str,
    questions_per_candidate: int = 5,
) -> ScreeningPack:
    with _L:
        pack_id = str(uuid.uuid4())
        pack = ScreeningPack(
            pack_id=pack_id,
            recruiter_id=recruiter_id,
            role_name=role_name,
            department=department,
            job_level=job_level,
            min_band=min_band,
            min_cefr=min_cefr,
            questions_per_candidate=questions_per_candidate,
        )
        _PACKS[pack_id] = pack
        return pack


def get_screening_pack(pack_id: str) -> Optional[ScreeningPack]:
    with _L:
        return _PACKS.get(pack_id)


def get_recruiter_packs(recruiter_id: str) -> list[ScreeningPack]:
    with _L:
        return [p for p in _PACKS.values() if p.recruiter_id == recruiter_id]


def add_candidate_to_pack(pack_id: str, learner_id: str) -> bool:
    with _L:
        pack = _PACKS.get(pack_id)
        if not pack:
            return False
        if learner_id not in pack.candidate_ids:
            pack.candidate_ids.append(learner_id)
        return True


def record_screening_session(pack_id: str, session_id: str) -> bool:
    with _L:
        pack = _PACKS.get(pack_id)
        if not pack:
            return False
        if session_id not in pack.completed_session_ids:
            pack.completed_session_ids.append(session_id)
        return True


# ============================================================================
# HELPERS
# ============================================================================

# IELTS band → CEFR level mapping (official Cambridge cross-reference)
_BAND_TO_CEFR = [
    (8.5, "c2"),
    (7.0, "c1"),
    (5.5, "b2"),
    (4.0, "b1"),
    (3.0, "a2"),
    (0.0, "a1"),
]


def band_to_cefr(band: float) -> str:
    for threshold, level in _BAND_TO_CEFR:
        if band >= threshold:
            return level
    return "a1"


def cefr_to_min_band(cefr: str) -> float:
    mapping = {"a1": 1.0, "a2": 3.0, "b1": 4.0, "b2": 5.5, "c1": 7.0, "c2": 8.5}
    return mapping.get(cefr.lower(), 1.0)
