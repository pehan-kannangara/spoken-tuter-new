"""Database-backed persistence for learners, sessions, classes, and screening."""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime
from typing import Optional, cast

from pydantic import BaseModel, Field
from sqlalchemy import select

from backend.db.models import (
        ClassORM,
        LearnerProfileORM,
        PracticeSessionORM,
        ProgressRecordORM,
        ScreeningPackORM,
)
from backend.db.session import db_session


class BusinessEnglishProfile(BaseModel):
    """Research-aligned profile for workplace speaking improvement."""

    industry_sector: str
    job_function: str
    communication_contexts: list[str] = Field(default_factory=list)
    client_facing: bool = False
    weekly_speaking_hours: int = 0
    target_use_case: str = "meeting_participation"
    timeline_weeks: int = 12


# ============================================================================
# DATA MODELS
# ============================================================================

class LearnerProfile(BaseModel):
    learner_id: str
    name: str
    email: str
    role: str                       # school_student | university_student | working_professional
    pathway: str                    # ielts | cefr | business_english
    goal: str                       # ielts_exam | general_improvement | for_school | working_purpose | interview_preparation | business_communication
    current_band: float = 0.0       # IELTS band (1–9); 0 = not yet assessed
    current_cefr: str = "unknown"   # a1 | a2 | b1 | b2 | c1 | c2
    target_band: Optional[float] = None
    target_cefr: Optional[str] = None
    business_profile: Optional[BusinessEnglishProfile] = None
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


def _learner_from_orm(row: LearnerProfileORM) -> LearnerProfile:
    return LearnerProfile(
        learner_id=row.learner_id,
        name=row.name,
        email=row.email,
        role=row.role,
        pathway=row.pathway,
        goal=row.goal,
        current_band=row.current_band,
        current_cefr=row.current_cefr,
        target_band=row.target_band,
        target_cefr=row.target_cefr,
        business_profile=BusinessEnglishProfile(**row.business_profile_json) if row.business_profile_json else None,
        class_id=row.class_id,
        session_ids=list(row.session_ids_json or []),
        streak_days=row.streak_days,
        badges=list(row.badges_json or []),
        created_at=row.created_at,
        last_active_at=row.last_active_at,
    )


def _response_dict_to_models(payload: dict | None) -> dict[int, SubmittedResponse]:
    data = payload or {}
    return {int(k): SubmittedResponse.model_validate(v) for k, v in data.items()}


def _score_dict_to_models(payload: dict | None) -> dict[int, AssessmentScore]:
    data = payload or {}
    return {int(k): AssessmentScore.model_validate(v) for k, v in data.items()}


def _session_from_orm(row: PracticeSessionORM) -> PracticeSession:
    return PracticeSession(
        session_id=row.session_id,
        learner_id=row.learner_id,
        pathway=row.pathway,
        session_type=row.session_type,
        status=row.status,
        question_ids=list(row.question_ids_json or []),
        current_index=row.current_index,
        responses=_response_dict_to_models(row.responses_json),
        scores=_score_dict_to_models(row.scores_json),
        started_at=row.started_at,
        completed_at=row.completed_at,
        overall_band=row.overall_band,
        overall_cefr=row.overall_cefr,
        band_before_session=row.band_before_session,
    )


def _class_from_orm(row: ClassORM) -> Class:
    return Class(
        class_id=row.class_id,
        teacher_id=row.teacher_id,
        class_name=row.class_name,
        class_code=row.class_code,
        learner_ids=list(row.learner_ids_json or []),
        created_at=row.created_at,
    )


def _pack_from_orm(row: ScreeningPackORM) -> ScreeningPack:
    return ScreeningPack(
        pack_id=row.pack_id,
        recruiter_id=row.recruiter_id,
        role_name=row.role_name,
        department=row.department,
        job_level=row.job_level,
        min_band=row.min_band,
        min_cefr=row.min_cefr,
        questions_per_candidate=row.questions_per_candidate,
        candidate_ids=list(row.candidate_ids_json or []),
        completed_session_ids=list(row.completed_session_ids_json or []),
        status=row.status,
        created_at=row.created_at,
    )


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
    business_profile: Optional[dict] = None,
) -> LearnerProfile:
    with db_session() as db:
        learner_id = str(uuid.uuid4())
        class_row = None
        if class_code:
            class_row = db.scalar(select(ClassORM).where(ClassORM.class_code == class_code))
        row = LearnerProfileORM(
            learner_id=learner_id,
            name=name,
            email=email,
            role=role,
            pathway=pathway,
            goal=goal,
            target_band=target_band,
            target_cefr=target_cefr,
            business_profile_json=business_profile,
            class_id=class_row.class_id if class_row else None,
            session_ids_json=[],
            badges_json=[],
            created_at=datetime.utcnow(),
            last_active_at=datetime.utcnow(),
        )
        db.add(row)
        if class_row:
            learner_ids = list(class_row.learner_ids_json or [])
            learner_ids.append(learner_id)
            class_row.learner_ids_json = learner_ids
        db.flush()
        return _learner_from_orm(row)


def get_learner(learner_id: str) -> Optional[LearnerProfile]:
    with db_session() as db:
        row = db.scalar(select(LearnerProfileORM).where(LearnerProfileORM.learner_id == learner_id))
        return _learner_from_orm(row) if row else None


def update_learner_level(learner_id: str, band: float, cefr: str) -> bool:
    with db_session() as db:
        row = db.scalar(select(LearnerProfileORM).where(LearnerProfileORM.learner_id == learner_id))
        if not row:
            return False
        row.current_band = band
        row.current_cefr = cefr
        row.last_active_at = datetime.utcnow()
        return True


def get_all_learners() -> list[LearnerProfile]:
    with db_session() as db:
        rows = db.scalars(select(LearnerProfileORM)).all()
        return [_learner_from_orm(row) for row in rows]


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
    with db_session() as db:
        session_id = str(uuid.uuid4())
        row = PracticeSessionORM(
            session_id=session_id,
            learner_id=learner_id,
            pathway=pathway,
            session_type=session_type,
            status="active",
            question_ids_json=question_ids,
            current_index=0,
            responses_json={},
            scores_json={},
            started_at=datetime.utcnow(),
            band_before_session=band_before,
        )
        db.add(row)
        learner = db.scalar(select(LearnerProfileORM).where(LearnerProfileORM.learner_id == learner_id))
        if learner:
            session_ids = list(learner.session_ids_json or [])
            session_ids.append(session_id)
            learner.session_ids_json = session_ids
            learner.last_active_at = datetime.utcnow()
        db.flush()
        return _session_from_orm(row)


def get_session(session_id: str) -> Optional[PracticeSession]:
    with db_session() as db:
        row = db.scalar(select(PracticeSessionORM).where(PracticeSessionORM.session_id == session_id))
        return _session_from_orm(row) if row else None


def advance_session(session_id: str) -> Optional[PracticeSession]:
    """Move to next question; mark completed when all questions answered."""
    with db_session() as db:
        row = db.scalar(select(PracticeSessionORM).where(PracticeSessionORM.session_id == session_id))
        if not row:
            return None
        if row.status != "active":
            return _session_from_orm(row)
        row.current_index += 1
        if row.current_index >= len(row.question_ids_json or []):
            _complete_session(db, row)
        db.flush()
        return _session_from_orm(row)


def save_response(response: SubmittedResponse) -> None:
    with db_session() as db:
        row = db.scalar(select(PracticeSessionORM).where(PracticeSessionORM.session_id == response.session_id))
        if not row:
            return
        responses = dict(row.responses_json or {})
        responses[str(response.question_index)] = response.model_dump(mode="json")
        row.responses_json = responses


def save_score(score: AssessmentScore) -> None:
    with db_session() as db:
        row = db.scalar(select(PracticeSessionORM).where(PracticeSessionORM.session_id == score.session_id))
        if not row:
            return
        scores = dict(row.scores_json or {})
        scores[str(score.question_index)] = score.model_dump(mode="json")
        row.scores_json = scores
        if len(scores) >= len(row.question_ids_json or []):
            bands = [item["overall_band"] for item in scores.values()]
            avg = round(sum(bands) / len(bands) * 2) / 2
            row.overall_band = avg
            row.overall_cefr = band_to_cefr(avg)
            if row.status == "active":
                _complete_session(db, row)


def _complete_session(db, row: PracticeSessionORM) -> None:
    row.status = "completed"
    row.completed_at = datetime.utcnow()
    if row.overall_band is None:
        scores = dict(row.scores_json or {})
        if scores:
            bands = [item["overall_band"] for item in scores.values()]
            row.overall_band = round(sum(bands) / len(bands) * 2) / 2
            if row.overall_band is not None:
                row.overall_cefr = band_to_cefr(cast(float, row.overall_band))
    if row.overall_band is not None:
        db.add(ProgressRecordORM(
            record_id=str(uuid.uuid4()),
            learner_id=row.learner_id,
            session_id=row.session_id,
            band=row.overall_band,
            cefr=row.overall_cefr or "unknown",
            recorded_at=datetime.utcnow(),
        ))
        learner = db.scalar(select(LearnerProfileORM).where(LearnerProfileORM.learner_id == row.learner_id))
        if learner:
            learner.current_band = row.overall_band
            learner.current_cefr = row.overall_cefr or learner.current_cefr
            learner.last_active_at = datetime.utcnow()


def get_learner_sessions(learner_id: str) -> list[PracticeSession]:
    with db_session() as db:
        rows = db.scalars(
            select(PracticeSessionORM)
            .where(PracticeSessionORM.learner_id == learner_id)
            .order_by(PracticeSessionORM.started_at)
        ).all()
        return [_session_from_orm(row) for row in rows]


# ============================================================================
# PROGRESS OPERATIONS
# ============================================================================

def get_progress(learner_id: str) -> list[ProgressRecord]:
    with db_session() as db:
        rows = db.scalars(
            select(ProgressRecordORM)
            .where(ProgressRecordORM.learner_id == learner_id)
            .order_by(ProgressRecordORM.recorded_at)
        ).all()
        return [
            ProgressRecord(
                record_id=row.record_id,
                learner_id=row.learner_id,
                session_id=row.session_id,
                band=row.band,
                cefr=row.cefr,
                recorded_at=row.recorded_at,
            )
            for row in rows
        ]


# ============================================================================
# CLASS OPERATIONS
# ============================================================================

def create_class(teacher_id: str, class_name: str) -> Class:
    with db_session() as db:
        class_id = str(uuid.uuid4())
        row = ClassORM(
            class_id=class_id,
            teacher_id=teacher_id,
            class_name=class_name,
            class_code=_generate_class_code(class_id),
            learner_ids_json=[],
            created_at=datetime.utcnow(),
        )
        db.add(row)
        db.flush()
        return _class_from_orm(row)


def get_class(class_id: str) -> Optional[Class]:
    with db_session() as db:
        row = db.scalar(select(ClassORM).where(ClassORM.class_id == class_id))
        return _class_from_orm(row) if row else None


def get_teacher_classes(teacher_id: str) -> list[Class]:
    with db_session() as db:
        rows = db.scalars(select(ClassORM).where(ClassORM.teacher_id == teacher_id)).all()
        return [_class_from_orm(row) for row in rows]


def _generate_class_code(seed: str) -> str:
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
    with db_session() as db:
        row = ScreeningPackORM(
            pack_id=str(uuid.uuid4()),
            recruiter_id=recruiter_id,
            role_name=role_name,
            department=department,
            job_level=job_level,
            min_band=min_band,
            min_cefr=min_cefr,
            questions_per_candidate=questions_per_candidate,
            candidate_ids_json=[],
            completed_session_ids_json=[],
            status="active",
            created_at=datetime.utcnow(),
        )
        db.add(row)
        db.flush()
        return _pack_from_orm(row)


def get_screening_pack(pack_id: str) -> Optional[ScreeningPack]:
    with db_session() as db:
        row = db.scalar(select(ScreeningPackORM).where(ScreeningPackORM.pack_id == pack_id))
        return _pack_from_orm(row) if row else None


def get_recruiter_packs(recruiter_id: str) -> list[ScreeningPack]:
    with db_session() as db:
        rows = db.scalars(select(ScreeningPackORM).where(ScreeningPackORM.recruiter_id == recruiter_id)).all()
        return [_pack_from_orm(row) for row in rows]


def add_candidate_to_pack(pack_id: str, learner_id: str) -> bool:
    with db_session() as db:
        row = db.scalar(select(ScreeningPackORM).where(ScreeningPackORM.pack_id == pack_id))
        if not row:
            return False
        candidate_ids = list(row.candidate_ids_json or [])
        if learner_id not in candidate_ids:
            candidate_ids.append(learner_id)
            row.candidate_ids_json = candidate_ids
        return True


def record_screening_session(pack_id: str, session_id: str) -> bool:
    with db_session() as db:
        row = db.scalar(select(ScreeningPackORM).where(ScreeningPackORM.pack_id == pack_id))
        if not row:
            return False
        session_ids = list(row.completed_session_ids_json or [])
        if session_id not in session_ids:
            session_ids.append(session_id)
            row.completed_session_ids_json = session_ids
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
