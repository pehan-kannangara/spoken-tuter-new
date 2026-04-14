"""
Assessment Store - Assessment and response persistence layer
SQLAlchemy ORM models for assessments with scoring
"""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, Float, Text, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
import secrets

Base = declarative_base()


class Assessment(Base):
    """Assessment model - stores assessment templates and metadata"""
    __tablename__ = "assessments"

    id = Column(String(36), primary_key=True, default=lambda: secrets.token_hex(18))
    learner_id = Column(String(36), nullable=False, index=True)
    template_id = Column(String(36), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    difficulty_level = Column(String(50), nullable=True)  # easy, medium, hard
    
    # Assessment state
    status = Column(String(50), nullable=False, default="draft")  # draft, in_progress, completed, reviewed
    
    # Scoring
    final_score = Column(Float, nullable=True)
    quality_decision = Column(String(50), nullable=True)  # accepted, rejected, requires_review
    rubric_applied = Column(Boolean, nullable=False, default=False)
    minimum_quality_score = Column(Integer, nullable=False, default=70)
    
    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)

    def to_dict(self):
        """Serialize to dict"""
        return {
            "id": self.id,
            "learner_id": self.learner_id,
            "template_id": self.template_id,
            "title": self.title,
            "description": self.description,
            "difficulty_level": self.difficulty_level,
            "status": self.status,
            "final_score": self.final_score,
            "quality_decision": self.quality_decision,
            "rubric_applied": self.rubric_applied,
            "minimum_quality_score": self.minimum_quality_score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
        }


class AssessmentResponse(Base):
    """Assessment Response model - stores learner responses and scores"""
    __tablename__ = "assessment_responses"

    id = Column(String(36), primary_key=True, default=lambda: secrets.token_hex(18))
    assessment_id = Column(String(36), ForeignKey("assessments.id"), nullable=False, index=True)
    question_id = Column(String(36), nullable=False, index=True)
    
    # Response data
    response_text = Column(Text, nullable=False)
    response_audio_url = Column(String(500), nullable=True)
    
    # Scoring
    score = Column(Float, nullable=True)  # 0-100
    
    # Quality gates
    schema_validation_passed = Column(Boolean, nullable=True)
    clarity_check_passed = Column(Boolean, nullable=True)
    format_validation_passed = Column(Boolean, nullable=True)
    bias_check_passed = Column(Boolean, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    scored_at = Column(DateTime, nullable=True)

    def to_dict(self):
        """Serialize to dict"""
        return {
            "id": self.id,
            "assessment_id": self.assessment_id,
            "question_id": self.question_id,
            "response_text": self.response_text[:100] + "..." if len(self.response_text) > 100 else self.response_text,
            "score": self.score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "scored_at": self.scored_at.isoformat() if self.scored_at else None,
        }


class AssessmentStore:
    """Assessment persistence layer"""

    def __init__(self, db_session):
        """Initialize with SQLAlchemy session"""
        self.db = db_session

    def create_assessment(
        self,
        learner_id: str,
        template_id: str,
        title: str,
        description: str = None,
        difficulty_level: str = None,
        minimum_quality_score: int = 70,
    ) -> Assessment:
        """
        Create new assessment

        Args:
            learner_id: ID of learner
            template_id: ID of assessment template
            title: Assessment title
            description: Optional description
            difficulty_level: Optional difficulty (easy/medium/hard)
            minimum_quality_score: Minimum score threshold (0-100)

        Returns:
            Assessment object
        """
        assessment = Assessment(
            learner_id=learner_id,
            template_id=template_id,
            title=title,
            description=description,
            difficulty_level=difficulty_level,
            status="draft",
            minimum_quality_score=minimum_quality_score,
        )
        self.db.add(assessment)
        self.db.commit()
        self.db.refresh(assessment)
        return assessment

    def get_assessment(self, assessment_id: str) -> Assessment:
        """Retrieve assessment by ID"""
        return self.db.query(Assessment).filter(Assessment.id == assessment_id).first()

    def get_assessment_responses(self, assessment_id: str) -> list:
        """Get all responses for an assessment"""
        return self.db.query(AssessmentResponse).filter(
            AssessmentResponse.assessment_id == assessment_id
        ).all()

    def create_response(
        self,
        assessment_id: str,
        question_id: str,
        response_text: str,
        response_audio_url: str = None,
    ) -> AssessmentResponse:
        """
        Record a learner response

        Args:
            assessment_id: ID of assessment
            question_id: ID of question
            response_text: Learner's text response
            response_audio_url: Optional audio recording URL

        Returns:
            AssessmentResponse object
        """
        response = AssessmentResponse(
            assessment_id=assessment_id,
            question_id=question_id,
            response_text=response_text,
            response_audio_url=response_audio_url,
        )
        self.db.add(response)
        self.db.commit()
        self.db.refresh(response)
        return response

    def update_response_score(
        self,
        response_id: str,
        score: float,
        schema_passed: bool = None,
        clarity_passed: bool = None,
        format_passed: bool = None,
        bias_passed: bool = None,
    ) -> AssessmentResponse:
        """
        Update response with score and quality gate results

        Args:
            response_id: ID of response
            score: Numeric score (0-100)
            schema_passed: Schema validation result
            clarity_passed: Clarity check result
            format_passed: Format validation result
            bias_passed: Bias check result

        Returns:
            Updated AssessmentResponse
        """
        response = self.db.query(AssessmentResponse).filter(
            AssessmentResponse.id == response_id
        ).first()

        if response:
            response.score = score
            response.schema_validation_passed = schema_passed
            response.clarity_check_passed = clarity_passed
            response.format_validation_passed = format_passed
            response.bias_check_passed = bias_passed
            response.scored_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(response)

        return response

    def update_assessment_score(
        self,
        assessment_id: str,
        final_score: float,
        quality_decision: str = None,
        rubric_applied: bool = False,
    ) -> Assessment:
        """
        Update assessment with final score and quality decision

        Args:
            assessment_id: ID of assessment
            final_score: Aggregated final score
            quality_decision: Decision result (accepted/rejected/requires_review)
            rubric_applied: Whether rubric policy was applied

        Returns:
            Updated Assessment
        """
        assessment = self.get_assessment(assessment_id)
        if assessment:
            assessment.final_score = final_score
            assessment.quality_decision = quality_decision
            assessment.rubric_applied = rubric_applied
            assessment.status = "completed"
            assessment.completed_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(assessment)

        return assessment

    def get_learner_assessments(self, learner_id: str) -> list:
        """Get all assessments for a learner"""
        return self.db.query(Assessment).filter(
            Assessment.learner_id == learner_id
        ).order_by(Assessment.created_at.desc()).all()

    def get_assessment_by_template(self, learner_id: str, template_id: str) -> Assessment:
        """Get most recent assessment for learner + template combo"""
        return self.db.query(Assessment).filter(
            Assessment.learner_id == learner_id,
            Assessment.template_id == template_id,
        ).order_by(Assessment.created_at.desc()).first()
