"""
QA ENGINE - COMPREHENSIVE QUALITY ASSURANCE FOR SPOKEN ENGLISH ASSESSMENTS

This QA Engine provides an automated, end-to-end quality assurance pipeline for generated
question items. It implements research-grade validation, lifecycle management, and drift
monitoring to ensure assessment reliability and CEFR/IELTS alignment.

## ARCHITECTURE OVERVIEW

The QA Engine operates in a strict gated pipeline:

    Generation (Draft)
         ↓ validate
    Validation Report
         ↓ evaluate gates
    [ Auto-pass? ] → YES → AUTO_VALIDATED
         ↓ NO
    Expert Review Queue (EXPERT_REVIEW_PENDING)
         ↓ review / approve
    EXPERT_APPROVED
         ↓ calibrate
    SHADOW_TESTING
         ↓ validate equivalence
    SHADOW_CALIBRATED
         ↓ publish
    ACTIVE
         ↓ monthly monitor
    MONITORING → [ Drift detected? ] → YES → DRIFT_FLAGGED / RETIRED
         ↓ NO
    Continue monitoring


## KEY COMPONENTS

### 1. Configuration (config.py)
- Standardized thresholds for all validation gates
- Acceptance criteria for advancement
- Monitoring and drift detection limits
- Research validation targets

### 2. Schemas (schemas.py)
- ItemSpecification: Blueprint for generation
- QuestionItem: Generated item before validation
- ItemLifecycle: Full state tracking
- QAValidationReport: Comprehensive validation result
- DriftMonitoringResult: Monthly metrics tracking
- ResearchExportRecord: Anonymized research dataset

### 3. Validators (validators/)
- schema_compliance.py: JSON schema and required fields
- validation.py: Instruction clarity, format rules, complexity bounds
- bias_safety.py: Cultural bias, stereotype risk, banned topics
- duplicate_check.py: Semantic similarity detection
- standards_elicitation.py: CEFR/IELTS alignment, response quality prediction

### 4. Orchestrator (orchestrator.py)
- Main entry point for QA validation
- Runs all validators in sequence
- Computes composite quality score
- Generates pass/fail recommendation

### 5. Lifecycle Manager (lifecycle.py)
- Item state machine with valid transitions
- Audit trail of all state changes
- Event logging for research reproducibility

### 6. QA Workflow Agent (agents/qa_workflow/graph.py)
- LangGraph integration for orchestrator routing
- Handlers for: generate, validate, activate, monitor, retire
- Integration with main API

### 7. Drift Monitoring (monitors/drift.py)
- Monthly automated monitoring of active items
- Difficulty drift detection (z-score)
- Fairness analysis across subgroups
- Score inflation detection
- Discrimination (item-total correlation) check


## HOW TO USE

### 1. Generate a New Item

POST /orchestrate
{
    "user_id": "curriculum_manager_1",
    "role": "admin",
    "event_type": "generate_item",
    "payload": {
        "spec_id": "spec_123",
        "spec_data": {
            "pathway": "cefr",
            "target_level": "b1",
            "task_type": "part_1",
            "domain": "business",
            "skill_focus": "fluency",
            "lexical_complexity_level": "medium",
            "syntactic_complexity_level": "medium"
        },
        "generation_method": "template"
    }
}

Response:
{
    "status": "ok",
    "message": "Item generated: item_xyz",
    "item_id": "item_xyz",
    "item": { ... QuestionItem dict ... },
    "lifecycle": { ... ItemLifecycle dict ... },
    "next_step": "validate_item"
}


### 2. Validate the Item

POST /orchestrate
{
    "user_id": "curriculum_manager_1",
    "role": "admin",
    "event_type": "validate_item",
    "payload": {
        "item_data": { ... QuestionItem dict from previous step ... },
        "existing_item_ids": ["item_abc", "item_def"]  // For duplicate check
    }
}

Response:
{
    "status": "ok",
    "message": "Validation complete. Quality score: 88.5/100",
    "item_id": "item_xyz",
    "report": { ... QAValidationReport dict ... },
    "recommended_action": "accept",
    "next_step": "activate_item",
    "quality_score": 88.5
}


### 3. Activate the Item (Auto or Manual)

If quality_score >= 85 and all required gates pass, auto-activate:

POST /orchestrate
{
    "user_id": "system",
    "role": "admin",
    "event_type": "activate_item",
    "payload": {
        "item_id": "item_xyz",
        "lifecycle_data": { ... ItemLifecycle dict ... }
    }
}

Response:
{
    "status": "ok",
    "message": "Transitioned item_xyz from AUTO_VALIDATED to ACTIVE",
    "item_id": "item_xyz",
    "current_status": "active",
    "lifecycle": { ... updated ItemLifecycle dict ... }
}

Item now appears in active question bank for assessments.


### 4. Monitor for Drift (Monthly Automated Job)

POST /orchestrate
{
    "user_id": "monitoring_job",
    "role": "system",
    "event_type": "monitor_drift",
    "payload": {
        "item_id": "item_xyz",
        "monitoring_data": {
            "sample_size": 250,
            "monitoring_period_days": 30,
            "baseline_difficulty": 5.0,
            "current_difficulty": 5.8,
            "difficulty_std": 1.2,
            "baseline_mean_score": 5.0,
            "current_mean_score": 5.5,
            "item_total_correlation": 0.35,
            "subgroup_metrics": {
                "L1_Chinese": { "mean_score": 5.2 },
                "L1_Spanish": { "mean_score": 5.8 }
            }
        }
    }
}

Response:
{
    "status": "ok",
    "message": "Drift monitoring executed",
    "item_id": "item_xyz",
    "alert_triggered": false,
    "recommendation": "monitor"
}

If alert_triggered=true or drift detected:
- Recommendation: "investigate" → flag in system for expert review
- Recommendation: "retire" → auto-retire item, remove from active bank


### 5. Retire an Item

POST /orchestrate
{
    "user_id": "system",
    "role": "admin",
    "event_type": "retire_item",
    "payload": {
        "item_id": "item_xyz",
        "reason": "Drift alert: difficulty increased >2 SD",
        "lifecycle_data": { ... ItemLifecycle dict ... }
    }
}

Response:
{
    "status": "ok",
    "message": "Transitioned item_xyz from ACTIVE to RETIRED",
    "item_id": "item_xyz",
    "current_status": "retired"
}

Item archived; available for research export but not for new assessments.


## VALIDATION GATES & CRITERIA

Each item must pass the following gates before activation:

1. **SCHEMA_COMPLIANCE** (Hard Fail)
   - All required fields present
   - Valid Pydantic types
   - Instruction not null
   - Confidence: 1.0 (deterministic)

2. **INSTRUCTION_CLARITY** (Error if fails)
   - Length: 20-500 characters
   - Max 2 questions (ambiguity prevention)
   - No unfilled templates
   - Contains task verb (describe, explain, discuss, etc.)
   - Confidence: 0.85

3. **FORMAT_COMPLIANCE** (Error if fails)
   - Valid task type (IELTS Part 1/2/3 or CEFR)
   - IELTS Part 2 must include prompt_text
   - Confidence: 0.90

4. **BIAS_SAFETY** (Error if fails)
   - No banned topics (religion, politics, etc.)
   - Restricted topics flagged for review (not auto-fail)
   - Culturally neutral language
   - No stereotype-triggering phrases
   - Confidence: 0.85

5. **DUPLICATE_CHECK** (Error if fails)
   - Token overlap < 70% with existing active items
   - Semantic similarity < 85%
   - Confidence: 0.95

6. **STANDARDS_ALIGNMENT** (Error if fails)
   - Predicted difficulty matches target level
   - Vocabulary complexity matches CEFR/IELTS
   - Sentence complexity matches expected range
   - Confidence: 0.75-0.80

7. **ELICITATION_QUALITY** (Warning if fails, not hard fail)
   - Open-ended prompt (not yes/no)
   - Invites elaboration or examples
   - Prediction: likely substantive response
   - Confidence: 0.85


## QUALITY SCORE CALCULATION

Composite score 0-100 calculated as weighted average:

    quality_score = Σ(gate_passed_bool × gate_weight) / Σ(gate_weights)

Weights:
    - schema_compliance: 0.15
    - standards_alignment: 0.20
    - elicitation_quality: 0.15
    - bias_safety: 0.20
    - calibration_accuracy: 0.15
    - equivalence_alignment: 0.15

Thresholds:
    - >= 85: Auto-activate
    - 70-84: Expert review required
    - < 70: Reject


## DRIFT MONITORING ALERTS

Monthly monitoring checks for:

1. **Difficulty Drift** (Item is getting easier or harder)
   - Threshold: |z-score| > 2.0 SD
   - Recommendation: Investigate or retire

2. **Score Inflation** (Students scoring higher on same item)
   - Threshold: |inflation %| > 15%
   - Recommendation: Investigate (learning effect? or ambiguity?)

3. **Fairness Drift** (Different subgroups performing differently)
   - DIF effect size threshold: > 0.15
   - Recommendation: Investigate for bias

4. **Low Discrimination** (Item doesn't differentiate high vs low students)
   - Item-total correlation threshold: < 0.20
   - Recommendation: Retire (weak item)

Auto-retire after 2 consecutive breach windows.


## AUDIT TRAIL & RESEARCH EXPORT

Every item's lifecycle is fully auditable:

```python
lifecycle.events → List[ItemEventLog]
  - created
  - auto_validated
  - expert_approved
  - shadow_calibrated
  - activated
  - monitored
  - drift_flagged
  - retired
```

Each event includes:
  - timestamp
  - from_status → to_status
  - reason
  - triggered_by (user_id or system)
  - decision_data (validation scores, drift metrics, etc.)

Export anonymized research dataset:
```python
ResearchExportRecord[]
  - item_anonymized_id
  - spec_pathway, target_level, domain
  - gates_passed
  - quality_score
  - pilot metrics (if available)
  - monitoring alerts
  - active_duration_days
  - cost_usd (operational cost)
```


## CONFIGURATION CUSTOMIZATION

Edit config.py to adjust thresholds:

```python
# Example: Stricter quality standards
SCHEMA_COMPLIANCE["hard_fail"]["missing_required_fields"] = True

AUTO_PUBLISH["auto_activate_on_pass"] = False  # Require expert review always

DRIFT_MONITOR["difficulty_drift_tolerance"] = 1.5  # More sensitive

RESEARCH_TARGETS["inter_rater_reliability_icc"] = 0.85  # Higher bar
```


## RESEARCH CONTRIBUTION

This QA engine enables the following peer-reviewed research:

1. **"Item Generation and Validation in AI-Assisted Language Assessment"**
   - Validation gate agreement rates
   - Quality score distribution analysis
   - Auto-vs-expert approval disagreement analysis

2. **"Longitudinal Reliability of Equivalent-Form Assessments"**
   - Correlation between reassessment forms
   - Test-retest reliability from pilot data

3. **"Drift Detection in Adaptive Question Banks"**
   - Monitoring effectiveness in detecting compromised items
   - Sensitivity/specificity of drift alerts
   - Cost-savings from early retirement

4. **"Fairness in AI-Generated Assessment Items"**
   - DIF analysis by linguistic background
   - Bias detection rates across demographic groups


## NEXT STEPS

1. Connect to database: Implement item storage and lifecycle persistence
2. LLM integration: Plug in actual generation service
3. Pilot calibration: Add shadow cohort collection and IRT fitting
4. Monitoring jobs: Set up scheduled drift checks
5. Research export: Implement anonymization and researcher access controls
"""
