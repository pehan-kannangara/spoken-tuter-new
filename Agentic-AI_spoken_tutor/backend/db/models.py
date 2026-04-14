from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.session import Base


class UserAccountORM(Base):
    __tablename__ = "user_accounts"

    user_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    role: Mapped[str] = mapped_column(String(50), index=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(128))
    password_salt: Mapped[str] = mapped_column(String(64))
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verification_token: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    profile_json: Mapped[dict] = mapped_column(JSON, default=dict)
    preferences_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class AuthSessionORM(Base):
    __tablename__ = "auth_sessions"

    token: Mapped[str] = mapped_column(String(128), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)


class LearnerProfileORM(Base):
    __tablename__ = "learner_profiles"

    learner_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(254), index=True)
    role: Mapped[str] = mapped_column(String(50), index=True)
    pathway: Mapped[str] = mapped_column(String(50), index=True)
    goal: Mapped[str] = mapped_column(String(80), index=True)
    current_band: Mapped[float] = mapped_column(Float, default=0.0)
    current_cefr: Mapped[str] = mapped_column(String(16), default="unknown")
    target_band: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_cefr: Mapped[str | None] = mapped_column(String(16), nullable=True)
    business_profile_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    class_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    session_ids_json: Mapped[list] = mapped_column(JSON, default=list)
    streak_days: Mapped[int] = mapped_column(Integer, default=0)
    badges_json: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_active_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PracticeSessionORM(Base):
    __tablename__ = "practice_sessions"

    session_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    learner_id: Mapped[str] = mapped_column(String(64), index=True)
    pathway: Mapped[str] = mapped_column(String(50), index=True)
    session_type: Mapped[str] = mapped_column(String(50), index=True)
    status: Mapped[str] = mapped_column(String(30), default="active")
    question_ids_json: Mapped[list] = mapped_column(JSON, default=list)
    current_index: Mapped[int] = mapped_column(Integer, default=0)
    responses_json: Mapped[dict] = mapped_column(JSON, default=dict)
    scores_json: Mapped[dict] = mapped_column(JSON, default=dict)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    overall_band: Mapped[float | None] = mapped_column(Float, nullable=True)
    overall_cefr: Mapped[str | None] = mapped_column(String(16), nullable=True)
    band_before_session: Mapped[float | None] = mapped_column(Float, nullable=True)


class ProgressRecordORM(Base):
    __tablename__ = "progress_records"

    record_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    learner_id: Mapped[str] = mapped_column(String(64), index=True)
    session_id: Mapped[str] = mapped_column(String(64), index=True)
    band: Mapped[float] = mapped_column(Float)
    cefr: Mapped[str] = mapped_column(String(16))
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ClassORM(Base):
    __tablename__ = "classes"

    class_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    teacher_id: Mapped[str] = mapped_column(String(64), index=True)
    class_name: Mapped[str] = mapped_column(String(120))
    class_code: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    learner_ids_json: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ScreeningPackORM(Base):
    __tablename__ = "screening_packs"

    pack_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    recruiter_id: Mapped[str] = mapped_column(String(64), index=True)
    role_name: Mapped[str] = mapped_column(String(120))
    department: Mapped[str] = mapped_column(String(120))
    job_level: Mapped[str] = mapped_column(String(50))
    min_band: Mapped[float] = mapped_column(Float)
    min_cefr: Mapped[str] = mapped_column(String(16))
    questions_per_candidate: Mapped[int] = mapped_column(Integer, default=5)
    candidate_ids_json: Mapped[list] = mapped_column(JSON, default=list)
    completed_session_ids_json: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(30), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class QuestionItemORM(Base):
    __tablename__ = "qa_items"

    item_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    payload_json: Mapped[dict] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ItemLifecycleORM(Base):
    __tablename__ = "qa_lifecycles"

    item_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    payload_json: Mapped[dict] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class QAValidationReportORM(Base):
    __tablename__ = "qa_reports"

    report_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    item_id: Mapped[str] = mapped_column(String(64), index=True)
    payload_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class RawDocumentORM(Base):
    __tablename__ = "raw_documents"

    document_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    document_type: Mapped[str] = mapped_column(String(50), index=True)
    document_key: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    payload_text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)