"""
QA ENGINE QUICK START GUIDE

Complete end-to-end examples for using the quality assurance pipeline.
"""

# ============================================================================
# EXAMPLE 1: Generate and Validate a CEFR B1 Question
# ============================================================================

def example_1_generate_and_validate():
    """
    Scenario: Curriculum manager needs to generate a B1-level business speaking prompt.
    """
    
    from backend.qa_engine.schemas import (
        ItemSpecification, 
        QuestionItem, 
        Pathway, 
        TargetLevel,
        LanguageDomain,
        SkillFocus,
        IELTSSpeakingPart
    )
    from backend.qa_engine.orchestrator import run_qa_validation_pipeline
    from datetime import datetime
    
    # Step 1: Define specification (blueprint)
    spec = ItemSpecification(
        spec_id="spec_001",
        pathway=Pathway.CEFR,
        target_level=TargetLevel.CEFR_B1,
        task_type=IELTSSpeakingPart.PART_1,
        expected_duration_seconds=(60, 120),
        domain=LanguageDomain.BUSINESS,
        skill_focus=SkillFocus.FLUENCY,
        lexical_complexity_level="medium",
        syntactic_complexity_level="medium",
        avoid_topics=["politics", "religion"],
        require_culturally_neutral=True,
        created_by="curriculum_manager_1",
    )
    
    # Step 2: Generate item (in production, LLM fills in the instruction)
    item = QuestionItem(
        item_id="item_b1_biz_001",
        spec_id=spec.spec_id,
        instruction="Describe your typical work day. What are your main responsibilities?",
        pathway=Pathway.CEFR,
        target_level=TargetLevel.CEFR_B1,
        task_type=IELTSSpeakingPart.PART_1,
        domain=LanguageDomain.BUSINESS,
        skill_focus=SkillFocus.FLUENCY,
        generated_by="template",
        generation_timestamp=datetime.utcnow(),
    )
    
    # Step 3: Run validation pipeline
    report = run_qa_validation_pipeline(
        item=item,
        existing_active_items=[],  # In production, fetch from DB
        run_all_gates=True,
        user_id="curriculum_manager_1",
    )
    
    # Step 4: Check results
    print(f"Quality Score: {report.quality_score}/100")
    print(f"Overall Pass: {report.overall_pass}")
    print(f"Recommended Action: {report.recommended_action}")
    print(f"Issues: {report.critical_issues}")
    
    # Expected output:
    # Quality Score: 87.5/100
    # Overall Pass: True
    # Recommended Action: accept
    # Issues: []


# ============================================================================
# EXAMPLE 2: Track Item Lifecycle from Draft to Active
# ============================================================================

def example_2_lifecycle_tracking():
    """
    Scenario: Follow an item from creation through validation and activation.
    """
    
    from backend.qa_engine.schemas import QuestionItem, ItemStatus
    from backend.qa_engine.lifecycle import create_lifecycle, transition_item, apply_validation_report
    from backend.qa_engine.orchestrator import run_qa_validation_pipeline
    from datetime import datetime
    
    # Step 1: Create item (same as Example 1)
    item = QuestionItem(
        item_id="item_lifecycle_001",
        spec_id="spec_001",
        instruction="Describe a memorable trip you have taken.",
        pathway="cefr",
        target_level="b1",
        task_type="part_1",
        domain="travel",
        skill_focus="mixed",
        generated_by="template",
        generation_timestamp=datetime.utcnow(),
    )
    
    # Step 2: Create lifecycle (DRAFT status)
    lifecycle = create_lifecycle(item, created_by="curriculum_manager_1")
    print(f"Initial Status: {lifecycle.current_status}")  # Output: draft
    
    # Step 3: Validate
    report = run_qa_validation_pipeline(item=item, user_id="system")
    
    # Step 4: Apply validation to lifecycle
    success, message, lifecycle = apply_validation_report(lifecycle, report, user_id="system")
    print(f"After Validation: {lifecycle.current_status}")  # Output: auto_validated (if passed)
    print(f"Events Count: {len(lifecycle.events)}")  # Output: 2 (created + validated)
    
    # Step 5: Manually advance to ACTIVE (skip shadow testing in this demo)
    success, message, lifecycle = transition_item(
        lifecycle,
        to_status=ItemStatus.ACTIVE,
        reason="Approved by curriculum manager for active use",
        triggered_by="curriculum_manager_1",
    )
    print(f"After Activation: {lifecycle.current_status}")  # Output: active
    
    # Step 6: View event history
    for event in lifecycle.events:
        print(f"  {event.timestamp}: {event.event_type} ({event.from_status} → {event.to_status})")
    

# ============================================================================
# EXAMPLE 3: Automatic Drift Monitoring
# ============================================================================

def example_3_drift_monitoring():
    """
    Scenario: Monthly automated job checks active items for metric drift.
    """
    
    from backend.qa_engine.monitors.drift import run_monthly_drift_check
    from backend.qa_engine.lifecycle import ItemLifecycle
    from backend.qa_engine.schemas import ItemStatus, Pathway, TargetLevel
    from datetime import datetime
    
    # Simulate an active item's lifecycle
    lifecycle = ItemLifecycle(
        item_id="item_active_001",
        current_status=ItemStatus.ACTIVE,
        created_at=datetime.utcnow(),
        first_activated_at=datetime.utcnow(),
        spec_id="spec_001",
        pathway=Pathway.CEFR,
        target_level=TargetLevel.CEFR_B1,
    )
    
    # Simulate 30 days of monitoring data
    monitoring_data = {
        "sample_size": 150,
        "monitoring_period_days": 30,
        # Baseline from when item was activated
        "baseline_difficulty": 5.0,
        "baseline_mean_score": 5.0,
        # Current month
        "current_difficulty": 6.2,  # Increased
        "current_mean_score": 5.8,
        "difficulty_std": 1.0,
        # Validity
        "item_total_correlation": 0.42,
        "subgroup_metrics": {
            "native_English": {"mean_score": 5.5},
            "L1_Chinese": {"mean_score": 6.1},
        },
    }
    
    # Run drift check
    result = run_monthly_drift_check(lifecycle, monitoring_data)
    
    print(f"Alert Triggered: {result.alert_triggered}")
    print(f"Recommendation: {result.action_recommended}")
    print(f"Alert Reasons: {result.alert_reasons}")
    
    # Expected output (item got harder):
    # Alert Triggered: True
    # Recommendation: investigate
    # Alert Reasons: ['Difficulty drift detected (z=1.20)']


# ============================================================================
# EXAMPLE 4: Duplicate Detection
# ============================================================================

def example_4_duplicate_detection():
    """
    Scenario: Check if new item is too similar to existing active items.
    """
    
    from backend.qa_engine.schemas import QuestionItem, Pathway, TargetLevel
    from backend.qa_engine.validators.duplicate_check import validate_duplicate_check
    from datetime import datetime
    
    # Existing active items
    existing_items = [
        QuestionItem(
            item_id="item_old_001",
            spec_id="spec_old",
            instruction="Describe your typical work day and your main responsibilities.",
            pathway=Pathway.CEFR,
            target_level=TargetLevel.CEFR_B1,
            task_type="part_1",
            domain="business",
            skill_focus="mixed",
            generated_by="template",
            generation_timestamp=datetime.utcnow(),
        ),
    ]
    
    # New item (too similar to existing)
    new_item = QuestionItem(
        item_id="item_new_001",
        spec_id="spec_new",
        instruction="Tell me about your work day and what you do at work.",  # Very similar
        pathway=Pathway.CEFR,
        target_level=TargetLevel.CEFR_B1,
        task_type="part_1",
        domain="business",
        skill_focus="mixed",
        generated_by="template",
        generation_timestamp=datetime.utcnow(),
    )
    
    # Check for duplicates
    result = validate_duplicate_check(new_item, existing_items)
    
    print(f"Passed Duplicate Check: {result.passed}")
    print(f"Issues: {result.issues_found}")
    
    # Expected output:
    # Passed Duplicate Check: False
    # Issues: ['Token overlap 0.75 exceeds threshold 0.70. Similar to item: item_old_001']


# ============================================================================
# EXAMPLE 5: Bias & Safety Check
# ============================================================================

def example_5_bias_safety():
    """
    Scenario: Validate that prompts avoid cultural bias and harmful content.
    """
    
    from backend.qa_engine.schemas import QuestionItem, Pathway, TargetLevel
    from backend.qa_engine.validators.bias_safety import validate_bias_safety
    from datetime import datetime
    
    # Item with problematic content
    risky_item = QuestionItem(
        item_id="item_risky_001",
        spec_id="spec_risky",
        instruction="Discuss why your country is superior to others.",  # Problematic
        pathway=Pathway.CEFR,
        target_level=TargetLevel.CEFR_B2,
        task_type="part_1",
        domain="culture",
        skill_focus="mixed",
        generated_by="template",
        generation_timestamp=datetime.utcnow(),
    )
    
    result = validate_bias_safety(risky_item)
    
    print(f"Passed Bias/Safety Check: {result.passed}")
    print(f"Issues: {result.issues_found}")
    
    # Expected output:
    # Passed Bias/Safety Check: False (stereotype language detected)
    # Issues: ['Contains stereotype-triggering language']


# ============================================================================
# EXAMPLE 6: Complete API Usage (Using Orchestrator)
# ============================================================================

def example_6_api_usage():
    """
    Scenario: Use the full orchestration endpoint to generate and validate.
    """
    
    from backend.agents.orchestrator.graph import run_orchestration
    import json
    
    # Step 1: Generate item via API
    generate_payload = {
        "user_id": "curriculum_manager_1",
        "role": "admin",
        "event_type": "generate_item",
        "payload": {
            "spec_id": "spec_api_001",
            "spec_data": {
                "pathway": "ielts",
                "target_level": "ielts_6",
                "task_type": "part_2",
                "domain": "academic",
                "skill_focus": "coherence",
                "lexical_complexity_level": "medium",
            },
            "generation_method": "template",
        },
    }
    
    gen_result = run_orchestration(**generate_payload)
    print(f"Generate Result: {gen_result['status']}")
    # Output: status: ok
    
    # Extract generated item data
    item_data = gen_result.get("item")
    
    # Step 2: Validate via API
    validate_payload = {
        "user_id": "curriculum_manager_1",
        "role": "admin",
        "event_type": "validate_item",
        "payload": {
            "item_data": item_data,
            "existing_item_ids": [],
        },
    }
    
    val_result = run_orchestration(**validate_payload)
    print(f"Validation Quality Score: {val_result.get('quality_score')}")
    # Output: Quality Score: 85.0+ (if passes)
    
    # Step 3: Activate if approved
    if val_result.get("recommended_action") == "accept":
        lifecycle_data = gen_result.get("lifecycle")
        activate_payload = {
            "user_id": "system",
            "role": "admin",
            "event_type": "activate_item",
            "payload": {
                "item_id": item_data["item_id"],
                "lifecycle_data": lifecycle_data,
            },
        }
        act_result = run_orchestration(**activate_payload)
        print(f"Item Status: {act_result.get('current_status')}")
        # Output: current_status: active


# ============================================================================
# Running Examples
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("Example 1: Generate and Validate")
    print("=" * 80)
    example_1_generate_and_validate()
    
    print("\n" + "=" * 80)
    print("Example 2: Lifecycle Tracking")
    print("=" * 80)
    # example_2_lifecycle_tracking()  # Uncomment to run
    
    print("\n" + "=" * 80)
    print("Example 3: Drift Monitoring")
    print("=" * 80)
    # example_3_drift_monitoring()  # Uncomment to run
    
    print("\n" + "=" * 80)
    print("Example 4: Duplicate Detection")
    print("=" * 80)
    # example_4_duplicate_detection()  # Uncomment to run
    
    print("\n" + "=" * 80)
    print("Example 5: Bias & Safety Check")
    print("=" * 80)
    # example_5_bias_safety()  # Uncomment to run
    
    print("\nTo run API examples, start FastAPI server and test with curl or Python requests.")
