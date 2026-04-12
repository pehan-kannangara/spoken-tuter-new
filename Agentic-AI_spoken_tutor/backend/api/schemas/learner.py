"""Pydantic request/response schemas for learner-facing endpoints."""

from typing import Optional
from pydantic import BaseModel, Field


class RegisterLearnerRequest(BaseModel):
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    role: str = Field(..., description="school_student | university_student | working_professional")
    pathway: str = Field(..., description="ielts | cefr")
    goal: str = Field(
        ...,
        description="ielts_exam | general_improvement | for_school | working_purpose | interview_preparation",
    )
    target_band: Optional[float] = Field(None, description="Target IELTS band (e.g. 7.0)")
    target_cefr: Optional[str] = Field(None, description="Target CEFR level (e.g. b2)")
    class_code: Optional[str] = Field(None, description="6-char teacher class code")


class StartSessionRequest(BaseModel):
    learner_id: str = Field(..., description="Learner UUID")
    session_type: str = Field("practice", description="practice | formal_assessment")
    num_questions: int = Field(5, ge=1, le=12, description="Number of questions in this session")
    task_type_filter: Optional[str] = Field(
        None,
        description="Optionally restrict to: part_1 | part_2 | part_3 | cefr_basic | cefr_intermediate | ...",
    )
    level_override: Optional[str] = Field(None, description="Force a specific CEFR/IELTS level filter")


class SubmitResponseRequest(BaseModel):
    transcript: str = Field(..., min_length=3, description="Spoken response text transcript")


class AdvanceSessionRequest(BaseModel):
    pass
