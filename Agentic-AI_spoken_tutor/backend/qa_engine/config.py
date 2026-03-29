"""
QA Engine Configuration

Standardized thresholds and acceptance criteria for item validation,
calibration, and monitoring pipelines. These values are research-grade
and designed for reproducibility and auditability.
"""

from enum import Enum
from typing import Dict, List, Tuple


class ValidationGate(str, Enum):
    """Sequential gates in the QA pipeline."""
    SCHEMA_COMPLIANCE = "schema_compliance"
    INSTRUCTION_CLARITY = "instruction_clarity"
    FORMAT_COMPLIANCE = "format_compliance"
    BIAS_SAFETY = "bias_safety"
    DUPLICATE_CHECK = "duplicate_check"
    STANDARDS_ALIGNMENT = "standards_alignment"
    ELICITATION_QUALITY = "elicitation_quality"
    SHADOW_CALIBRATION = "shadow_calibration"
    EQUIVALENCE_TEST = "equivalence_test"
    DRIFT_MONITOR = "drift_monitor"


class ItemStatus(str, Enum):
    """Complete lifecycle states for question items."""
    DRAFT = "draft"
    AUTO_VALIDATED = "auto_validated"
    EXPERT_REVIEW_PENDING = "expert_review_pending"
    EXPERT_APPROVED = "expert_approved"
    SHADOW_TESTING = "shadow_testing"
    SHADOW_CALIBRATED = "shadow_calibrated"
    ACTIVE = "active"
    MONITORING = "monitoring"
    DRIFT_FLAGGED = "drift_flagged"
    RETIRED = "retired"
    REJECTED = "rejected"


# ============================================================================
# SCHEMA & FORMAT VALIDATION THRESHOLDS
# ============================================================================

SCHEMA_COMPLIANCE = {
    "hard_fail": {
        "missing_required_fields": True,  # Fail if blueprint fields missing
        "invalid_json_schema": True,  # Fail on schema parse error
        "null_instruction": True,  # Fail if instruction is null/empty
    },
    "acceptance_threshold": 1.0,  # 100% - must pass all hard fails
}

INSTRUCTION_CLARITY = {
    "max_instruction_length": 500,  # Characters
    "min_instruction_length": 20,
    "forbidden_patterns": [
        r".*\?.*\?.*\?.*",  # More than 2 questions in sequence (ambiguity)
        r".*\[PLACEHOLDER\].*",  # Unfilled template slots
    ],
    "clarity_confidence_threshold": 0.85,  # LLM-based clarity check
}

TASK_FORMAT_COMPLIANCE = {
    "ielts": {
        "part_1": {
            "min_questions": 4,
            "max_questions": 6,
            "duration_seconds": (60, 120),  # Expected answer duration range
        },
        "part_2": {
            "has_topic_card": True,
            "duration_seconds": (120, 180),
        },
        "part_3": {
            "min_questions": 4,
            "max_questions": 6,
            "duration_seconds": (120, 180),
        },
    },
    "cefr": {
        "duration_seconds": (90, 300),
    },
}

# ============================================================================
# BIAS, FAIRNESS, AND SAFETY GATES
# ============================================================================

BIAS_SAFETY = {
    "banned_topics": [
        "religion",
        "politics_polarized",
        "medical_advice",
        "financial_advice",
        "illegal_activities",
    ],
    "restricted_topics": [
        "gender",
        "ethnicity",
        "disability",
        "socioeconomic_status",
    ],
    # If restricted topics appear, extra review required but not auto-reject
    "cultural_bias_confidence_threshold": 0.92,  # LLM toxicity check
    "stereotype_risk_threshold": 0.15,  # DIF proxy threshold for review
}

# ============================================================================
# DUPLICATION AND NOVELTY CONTROL
# ============================================================================

DUPLICATE_CHECK = {
    "semantic_similarity_threshold": 0.85,  # Cosine similarity
    "token_overlap_threshold": 0.70,
    "action": "hard_reject",  # Reject if too similar to existing active items
}

# ============================================================================
# STANDARDS ALIGNMENT (CEFR / IELTS PREDICTION)
# ============================================================================

STANDARDS_ALIGNMENT = {
    "model_confidence_threshold": 0.85,  # Classifier/regressor confidence
    "max_calibration_error": 0.20,  # IELTS-band equivalent or CEFR level
    # If target is B1 and model predicts B1 ± 0.20, accept
    "recalibration_window": 30,  # Days before re-check needed
}

# ============================================================================
# ELICITATION QUALITY CHECKS
# ============================================================================

ELICITATION_QUALITY = {
    "min_expected_response_time": 30,  # Seconds - too quick means weak elicitation
    "expected_lexical_range": "medium_to_high",  # Proxy for complexity
    "expected_syntax_variety": True,  # Should elicit varied sentence structures
    "expected_discourse_length": 120,  # Minimum words expected in response
    "relevance_prompt_strength_threshold": 0.70,  # LLM coherence likelihood
}

# ============================================================================
# SHADOW TESTING & PILOT CALIBRATION
# ============================================================================

SHADOW_CALIBRATION = {
    "min_pilot_cohort_size": 20,  # Minimum pilots to calibrate
    "completion_rate_threshold": 0.80,  # At least 80% must complete
    "response_time_cv_threshold": 0.40,  # Coefficient of variation < 40%
    # If too variable, prompt may be ambiguous
    "asr_confidence_threshold": 0.75,  # Avg transcription confidence
    "min_words_per_response": 50,  # Too short = weak elicitation
}

# ============================================================================
# EQUIVALENCE TESTING FOR REASSESSMENT FORMS
# (IRT/Rasch-based or simple mean/std comparison)
# ============================================================================

EQUIVALENCE_TEST = {
    "mean_difference_tolerance": 0.20,  # IELTS-band equivalent units
    "std_difference_tolerance": 0.15,  # Std dev can't drift > 0.15 bands
    "min_linking_sample_size": 100,  # Min students taking both forms
    "subgroup_dif_threshold": 0.15,  # Differential item functioning flag
    "bonferroni_correction": True,  # Apply multiple-comparison correction
}

# ============================================================================
# CONTINUOUS MONITORING & DRIFT DETECTION
# ============================================================================

DRIFT_MONITOR = {
    "monitoring_window_days": 30,  # Evaluate every 30 days when active
    "difficulty_drift_tolerance": 2.0,  # Standard deviations from baseline
    "fairness_drift_tolerance": 2.0,  # Subgroup performance drift
    "score_inflation_tolerance": 0.15,  # Mean score change threshold
    "low_discrimination_threshold": 0.20,  # Item-total correlation floor
    "auto_retire_after_breaches": 2,  # Auto-retire after 2 consecutive drift alerts
    "alert_threshold": 1.5,  # Alert before hard limit (early warning)
}

# ============================================================================
# AUTO-PUBLISH RULES (When Does an Item Become ACTIVE?)
# ============================================================================

AUTO_PUBLISH = {
    # All gates must pass
    "required_gates": [
        ValidationGate.SCHEMA_COMPLIANCE,
        ValidationGate.INSTRUCTION_CLARITY,
        ValidationGate.FORMAT_COMPLIANCE,
        ValidationGate.BIAS_SAFETY,
        ValidationGate.DUPLICATE_CHECK,
        ValidationGate.STANDARDS_ALIGNMENT,
        ValidationGate.ELICITATION_QUALITY,
    ],
    # For high-stakes (reassessment), also require:
    "high_stakes_gates": [
        ValidationGate.SHADOW_CALIBRATION,
        ValidationGate.EQUIVALENCE_TEST,
    ],
    # Auto-activate when all gates pass, no waiting required
    "auto_activate_on_pass": True,
}

# ============================================================================
# AUDIT & RESEARCH REPORTING
# ============================================================================

AUDIT_CONFIG = {
    "log_all_validation_runs": True,
    "log_all_state_transitions": True,
    "export_anonymized_reports": True,
    "retention_days": 365 * 7,  # 7 years for research/compliance
    "research_export_formats": ["csv", "json", "parquet"],
}

# ============================================================================
# ITEM BANK CONFIGURATION
# ============================================================================

ITEM_BANK = {
    "min_active_items_per_level": {
        "ielts": {"band_3": 8, "band_4": 10, "band_5": 12, "band_6": 15, "band_7": 12, "band_8": 10},
        "cefr": {"a1": 5, "a2": 8, "b1": 10, "b2": 12, "c1": 10, "c2": 8},
    },
    "retirement_policy": {
        "auto_retire_if_flagged_count": 3,  # Retire if flagged 3+ times
        "archive_after_days": 90,  # Move to archive 90 days after retired
    },
    "question_reuse_cooldown_days": 180,  # Can't reuse same retired Q for 6 months
}

# ============================================================================
# QUALITY SCORE CALCULATION (Composite for reporting)
# ============================================================================

QUALITY_SCORE_WEIGHTS = {
    # Weighted average across all passed gates
    "schema_compliance": 0.15,
    "standards_alignment": 0.20,
    "elicitation_quality": 0.15,
    "bias_safety": 0.20,
    "calibration_accuracy": 0.15,
    "equivalence_alignment": 0.15,
    # Final quality score 0-100; >85 is excellent
}

# ============================================================================
# RESEARCH VALIDATION TARGETS (for publication)
# ============================================================================

RESEARCH_TARGETS = {
    "inter_rater_reliability_icc": 0.80,  # ICC > 0.80 acceptable
    "ai_human_correlation": 0.85,  # Pearson r > 0.85
    "equivalent_form_correlation": 0.85,  # For reassessment reliability
    "fairness_subgroup_dif_max": 0.15,  # DIF effect size tolerance
    "cost_per_assessment_usd": 5.0,  # Budget cap
}

print("[QA Config] Thresholds loaded: research-grade, reproducible, auditable.")
