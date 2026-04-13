"""
QA Engine Schemas

Pydantic models for item specification, validation results,
audit trails, and research-grade reporting.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from enum import Enum

from backend.qa_engine.config import ItemStatus, ValidationGate


# ============================================================================
# ITEM SPECIFICATION (Blueprint for Generation)
# ============================================================================

class TargetLevel(str, Enum):
    """CEFR and IELTS levels."""
    CEFR_A1 = "a1"
    CEFR_A2 = "a2"
    CEFR_B1 = "b1"
    CEFR_B2 = "b2"
    CEFR_C1 = "c1"
    CEFR_C2 = "c2"
    IELTS_3 = "ielts_3"
    IELTS_4 = "ielts_4"
    IELTS_5 = "ielts_5"
    IELTS_6 = "ielts_6"
    IELTS_7 = "ielts_7"
    IELTS_8 = "ielts_8"
    IELTS_9 = "ielts_9"


class Pathway(str, Enum):
    """Learning pathways."""
    CEFR = "cefr"
    IELTS = "ielts"
    BUSINESS_ENGLISH = "business_english"


class IELTSSpeakingPart(str, Enum):
    """IELTS speaking task structure."""
    PART_1 = "part_1"  # Short personal questions
    PART_2 = "part_2"  # Long turn with cue card
    PART_3 = "part_3"  # Analytical discussion


class LanguageDomain(str, Enum):
    """Content themes to ensure variety."""
    BUSINESS = "business"
    ACADEMIC = "academic"
    EVERYDAY = "everyday"
    TRAVEL = "travel"
    TECHNOLOGY = "technology"
    CULTURE = "culture"
    HEALTH = "health"
    ENVIRONMENT = "environment"


class SkillFocus(str, Enum):
    """Which dimension is being targeted."""
    FLUENCY = "fluency"
    COHERENCE = "coherence"
    LEXICAL_RESOURCE = "lexical_resource"
    GRAMMAR = "grammar"
    PRONUNCIATION = "pronunciation"
    MIXED = "mixed"


class ItemSpecification(BaseModel):
    """
    Blueprint for generating a new question item.
    Constrains generation to ensure quality before LLM involvement.
    """
    
    # Core identity
    spec_id: str = Field(..., description="Unique specification ID")
    pathway: Pathway = Field(..., description="CEFR or IELTS")
    target_level: TargetLevel = Field(..., description="Target proficiency level")
    
    # Task structure
    task_type: IELTSSpeakingPart | str = Field(
        ..., 
        description="IELTS part 1/2/3 or CEFR task type"
    )
    expected_duration_seconds: tuple[int, int] = Field(
        (60, 300), 
        description="Min-max expected answer duration"
    )
    
    # Content constraints
    domain: LanguageDomain = Field(..., description="Topic area")
    skill_focus: SkillFocus = Field(
        SkillFocus.MIXED, 
        description="Primary skill dimension being elicited"
    )
    
    # Complexity bounds (proxy for CEFR/IELTS)
    lexical_complexity_level: str = Field(
        "medium",
        description="low|medium|high - guides prompt wording"
    )
    syntactic_complexity_level: str = Field(
        "medium",
        description="low|medium|high"
    )
    
    # Constraints on generation
    avoid_topics: List[str] = Field(
        default_factory=list,
        description="Topics to exclude (religious, political, etc.)"
    )
    require_culturally_neutral: bool = Field(
        True,
        description="Must avoid cultural biases"
    )
    max_niche_knowledge_required: bool = Field(
        False,
        description="Reject if requires specialized domain knowledge"
    )
    
    # Optional guidance
    generation_hints: Optional[str] = Field(
        None,
        description="Additional guidance for LLM generation"
    )
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(..., description="Spec author or system")
    
    class Config:
        use_enum_values = True


# ============================================================================
# GENERATED ITEM (Before Validation)
# ============================================================================

class QuestionItem(BaseModel):
    """
    A generated speaking prompt before quality validation.
    """
    
    item_id: str = Field(..., description="Unique item UUID")
    spec_id: str = Field(..., description="Source specification")
    
    # Generated content
    instruction: str = Field(..., description="Student-facing task instruction")
    prompt_text: Optional[str] = Field(None, description="Additional context (for Part 2 cue card)")
    expected_response_template: Optional[str] = Field(
        None, 
        description="Example response for internal reference"
    )
    
    # Metadata from spec
    pathway: Pathway
    target_level: TargetLevel
    task_type: IELTSSpeakingPart | str
    domain: LanguageDomain
    skill_focus: SkillFocus
    
    # Generation metadata
    generated_by: str = Field(..., description="'template'|'llm'|'hybrid'")
    generation_prompt: Optional[str] = Field(None, description="LLM prompt used")
    generation_timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Status
    status: ItemStatus = Field(ItemStatus.DRAFT, description="Current lifecycle stage")
    
    class Config:
        use_enum_values = True


# ============================================================================
# VALIDATION RESULT (Per Gate)
# ============================================================================

class ValidationResult(BaseModel):
    """Result of a single validation gate."""
    
    gate: ValidationGate = Field(..., description="Which validation gate")
    passed: bool = Field(..., description="Pass/fail")
    confidence: float = Field(..., description="0-1 confidence in result")
    
    # Details
    checks_performed: Dict[str, bool] = Field(
        default_factory=dict,
        description="Sub-checks within this gate"
    )
    issues_found: List[str] = Field(
        default_factory=list,
        description="Human-readable issues"
    )
    severity: str = Field(
        "info",
        description="info|warning|error"
    )
    
    # For audit
    validator_name: str = Field(..., description="Which validator ran this")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True


# ============================================================================
# FULL QA REPORT (All Gates for One Item)
# ============================================================================

class QAValidationReport(BaseModel):
    """
    Comprehensive validation summary for one item.
    Determines whether item advances to next lifecycle stage.
    """
    
    report_id: str = Field(..., description="Unique report UUID")
    item_id: str = Field(..., description="Item being validated")
    
    # Gate results
    validation_results: List[ValidationResult] = Field(..., description="All gates run")
    
    # Overall decision
    overall_pass: bool = Field(..., description="Did item pass all required gates?")
    quality_score: float = Field(
        ..., 
        description="0-100 composite quality score"
    )
    recommended_action: str = Field(
        ..., 
        description="accept|review|reject"
    )
    
    # Details
    critical_issues: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    next_stage_if_accepted: Optional[ItemStatus] = Field(
        None,
        description="Lifecycle state if accepted"
    )
    
    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(..., description="QA reviewer or 'automated'")
    
    class Config:
        use_enum_values = True


# ============================================================================
# ITEM LIFECYCLE STATE RECORD
# ============================================================================

class ItemEventLog(BaseModel):
    """Single event in an item's lifecycle for audit trail."""
    
    event_id: str = Field(..., description="Unique event UUID")
    item_id: str = Field(..., description="Item affected")
    
    # Event detail
    event_type: str = Field(..., description="created|validated|approved|activated|monitored|retired")
    from_status: ItemStatus = Field(..., description="Previous status")
    to_status: ItemStatus = Field(..., description="New status")
    
    # Context
    reason: str = Field(..., description="Why this transition occurred")
    triggered_by: str = Field(..., description="User ID, system job, or automation rule")
    decision_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Gate results, drift metrics, etc."
    )
    
    # Timestamp
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True


class ItemLifecycle(BaseModel):
    """Full lifecycle tracking for one item."""
    
    item_id: str = Field(..., description="Unique item UUID")
    current_status: ItemStatus = Field(..., description="Current lifecycle state")
    
    # Key dates
    created_at: datetime = Field(...)
    first_activated_at: Optional[datetime] = Field(None)
    retired_at: Optional[datetime] = Field(None)
    
    # Event history
    events: List[ItemEventLog] = Field(default_factory=list)
    
    # Metadata
    spec_id: str = Field(..., description="Source specification")
    pathway: Pathway = Field(...)
    target_level: TargetLevel = Field(...)
    
    class Config:
        use_enum_values = True


# ============================================================================
# CALIBRATION & PILOT RESULTS
# ============================================================================

class PilotCohortResult(BaseModel):
    """Statistics from shadow testing cohort."""
    
    cohort_id: str = Field(..., description="Pilot cohort UUID")
    item_id: str = Field(...)
    
    # Sample
    sample_size: int = Field(..., description="N students")
    completion_rate: float = Field(..., description="0-1 completion ratio")
    
    # Response metrics
    mean_response_duration: float = Field(..., description="Seconds")
    std_response_duration: float = Field(...)
    min_words_per_response: float = Field(...)
    mean_words: float = Field(...)
    
    # Transcription quality
    mean_asr_confidence: float = Field(..., description="0-1")
    asr_confidence_std: float = Field(...)
    
    # Scoring metrics (if available)
    mean_predicted_band: Optional[float] = Field(None, description="For IELTS")
    std_predicted_band: Optional[float] = Field(None)
    
    #Flags
    passes_elicitation_check: bool = Field(...)
    flags: List[str] = Field(default_factory=list)
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True


# ============================================================================
# EQUIVALENCE TEST RESULT (For Reassessment Linking)
# ============================================================================

class EquivalenceTestResult(BaseModel):
    """Formal equivalence check between two question sets."""
    
    test_id: str = Field(..., description="Unique test UUID")
    form_a_item_ids: List[str] = Field(..., description="Reference form")
    form_b_item_ids: List[str] = Field(..., description="New form being linked")
    
    # Linking sample
    linking_sample_size: int = Field(..., description="N students on both forms")
    
    # Equating results
    mean_diff: float = Field(..., description="Form B mean - Form A mean (band units)")
    mean_diff_se: float = Field(..., description="Standard error of difference")
    passes_mean_test: bool = Field(...)
    
    std_diff: float = Field(...)
    passes_std_test: bool = Field(...)
    
    # DIF analysis by subgroup
    subgroup_difs: Dict[str, float] = Field(
        default_factory=dict,
        description="DIF effect sizes by demographic"
    )
    passes_fairness_test: bool = Field(...)
    
    # Overall decision
    forms_equivalent: bool = Field(...)
    recommendation: str = Field(..., description="accept|flag|investigate")
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True


# ============================================================================
# DRIFT MONITORING RESULT
# ============================================================================

class DriftMonitoringResult(BaseModel):
    """Monthly drift check on active item."""
    
    monitor_id: str = Field(..., description="Unique monitor run UUID")
    item_id: str = Field(...)
    
    # Monitoring window
    monitoring_period_days: int = Field(..., description="Days of data examined")
    sample_size: int = Field(..., description="N responses in window")
    
    # Difficulty drift
    baseline_difficulty: float = Field(..., description="IRT difficulty or raw mean")
    current_difficulty: float = Field(...)
    difficulty_z_score: float = Field(..., description="How many SDs from baseline")
    difficulty_drifted: bool = Field(...)
    
    # Fairness drift
    subgroup_drift_max: float = Field(..., description="Max DIF across subgroups")
    fairness_drifted: bool = Field(...)
    
    # Score inflation
    baseline_mean_score: float = Field(...)
    current_mean_score: float = Field(...)
    inflation_pct: float = Field(...)
    inflation_flagged: bool = Field(...)
    
    # Discrimination
    item_total_correlation: float = Field(..., description="Validity indicator")
    discrimination_low: bool = Field(...)
    
    # Overall alert
    alert_triggered: bool = Field(...)
    alert_reasons: List[str] = Field(default_factory=list)
    
    # Action taken
    action_recommended: str = Field(
        default="monitor",
        description="monitor|review|retire|investigate"
    )
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True


# ============================================================================
# RESEARCH EXPORT SCHEMA (For Peer Review & Validation)
# ============================================================================

class ResearchExportRecord(BaseModel):
    """
    Single row in anonymized research export.
    Used for publishing validation studies and cost-effectiveness analyses.
    """
    
    export_id: str = Field(..., description="Anonymized record ID")
    
    # Item identity (anonymized)
    item_anonymized_id: str = Field(...)
    spec_pathway: Pathway = Field(...)
    spec_target_level: TargetLevel = Field(...)
    spec_domain: LanguageDomain = Field(...)
    
    # Validation gates passed
    gates_passed: List[ValidationGate] = Field(...)
    quality_score: float = Field(...)
    time_to_active_days: Optional[int] = Field(None)
    
    # Calibration results (if available)
    pilot_mean_duration_sec: Optional[float] = Field(None)
    pilot_mean_words: Optional[float] = Field(None)
    pilot_completion_rate: Optional[float] = Field(None)
    
    # Equivalence (if applicable)
    equivalent_form_correlation: Optional[float] = Field(None)
    mean_linking_diff: Optional[float] = Field(None)
    
    # Monitoring (if retired)
    monitoring_alerts_count: int = Field(0)
    final_status: ItemStatus = Field(...)
    active_duration_days: Optional[int] = Field(None)
    
    # Operational cost
    api_calls_spent: int = Field(0, description="Validation API calls")
    cost_usd: float = Field(0.0, description="Operational cost of this item")
    
    # Exported for research
    export_timestamp: datetime = Field(default_factory=datetime.utcnow)
    research_use: str = Field(
        "validation_study",
        description="validation_study|reliability_study|cost_study"
    )
    
    class Config:
        use_enum_values = True
