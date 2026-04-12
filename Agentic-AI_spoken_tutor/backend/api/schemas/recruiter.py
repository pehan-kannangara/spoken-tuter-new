"""Pydantic request schemas for recruiter-facing endpoints."""

from typing import Optional
from pydantic import BaseModel, Field


class CreateScreeningPackRequest(BaseModel):
    recruiter_id: str = Field(..., description="Recruiter user UUID")
    role_name: str = Field(..., description="Job title or role name")
    department: str = Field(..., description="Department or team")
    job_level: str = Field("mid", description="junior | mid | senior | executive")
    min_band: float = Field(6.0, ge=1.0, le=9.0, description="Minimum IELTS overall band required")
    min_cefr: str = Field("b2", description="Minimum CEFR level: a1 | a2 | b1 | b2 | c1 | c2")
    questions_per_candidate: int = Field(5, ge=2, le=10, description="Questions per screening session")


class AddCandidateRequest(BaseModel):
    pack_id: str = Field(..., description="Screening pack UUID")
    learner_id: str = Field(..., description="Candidate learner UUID")


class StartCandidateSessionRequest(BaseModel):
    pack_id: str = Field(..., description="Screening pack UUID")
    learner_id: str = Field(..., description="Candidate learner UUID")
