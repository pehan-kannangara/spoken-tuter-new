"""Pydantic request schemas for teacher-facing endpoints."""

from pydantic import BaseModel, Field


class CreateClassRequest(BaseModel):
    teacher_id: str = Field(..., description="Teacher user UUID")
    class_name: str = Field(..., description="Display name for the class")


class ClassOverviewRequest(BaseModel):
    teacher_id: str = Field(..., description="Teacher user UUID")
    class_id: str = Field(..., description="Class UUID")


class LearnerDetailRequest(BaseModel):
    teacher_id: str = Field(..., description="Teacher user UUID")
    learner_id: str = Field(..., description="Learner UUID")
