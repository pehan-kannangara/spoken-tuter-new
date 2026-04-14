"""
Assessment Scoring Agent State - Data structures for scoring pipeline
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional


class AssessmentScoringState(BaseModel):
    """State for assessment scoring agent"""
    assessment_id: str = Field(..., description="Assessment ID")
    response_id: str = Field(..., description="Response ID")
    question_id: str = Field(..., description="Question ID")
    response_text: str = Field(..., description="Learner's response text")
    learner_id: str = Field(..., description="Learner ID")
    
    # Context from orchestration
    context_package: Optional[Dict[str, Any]] = None
    
    # Scoring outputs
    raw_score: Optional[float] = None
    quality_score: Optional[float] = None
    final_score: Optional[float] = None
    quality_decision: Optional[str] = None
    rubric_applied: bool = False
    
    # Quality gates results
    gates_passed: List[str] = Field(default_factory=list)
    gates_failed: List[str] = Field(default_factory=list)
    
    class Config:
        from_attributes = True
