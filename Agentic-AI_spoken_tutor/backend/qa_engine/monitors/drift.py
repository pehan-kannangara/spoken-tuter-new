"""
Drift Monitoring Jobs

Scheduled jobs for continuous monitoring of active items.
Detects metric drift, fairness drift, score inflation, and low discrimination.
"""

from datetime import datetime, timedelta
from typing import List, Optional
import uuid

from backend.qa_engine.config import DRIFT_MONITOR, ItemStatus
from backend.qa_engine.schemas import DriftMonitoringResult, ItemLifecycle


def run_monthly_drift_check(
    item_lifecycle: ItemLifecycle,
    monitoring_data: dict,
) -> DriftMonitoringResult:
    """
    Execute drift check on an active item.
    
    Args:
        item_lifecycle: Item to monitor
        monitoring_data: Dict with recent metrics:
            - baseline_difficulty
            - current_difficulty
            - baseline_mean_score
            - current_mean_score
            - item_total_correlation
            - subgroup_metrics
    
    Returns:
        DriftMonitoringResult with alert status and recommendations
    """
    
    # Extract monitoring window data
    sample_size = monitoring_data.get("sample_size", 0)
    monitoring_period_days = monitoring_data.get("monitoring_period_days", 30)
    
    baseline_difficulty = monitoring_data.get("baseline_difficulty", 0.0)
    current_difficulty = monitoring_data.get("current_difficulty", 0.0)
    
    baseline_mean_score = monitoring_data.get("baseline_mean_score", 5.0)
    current_mean_score = monitoring_data.get("current_mean_score", 5.0)
    
    item_total_correlation = monitoring_data.get("item_total_correlation", 0.5)
    subgroup_metrics = monitoring_data.get("subgroup_metrics", {})
    
    # Compute difficulty drift (z-score)
    difficulty_std = monitoring_data.get("difficulty_std", 1.0)
    if difficulty_std > 0:
        difficulty_z_score = (current_difficulty - baseline_difficulty) / difficulty_std
    else:
        difficulty_z_score = 0.0
    
    difficulty_drifted = abs(difficulty_z_score) > DRIFT_MONITOR.get("difficulty_drift_tolerance", 2.0)
    
    # Compute score inflation
    inflation_pct = (current_mean_score - baseline_mean_score) / baseline_mean_score * 100 if baseline_mean_score > 0 else 0
    inflation_flagged = abs(inflation_pct) > DRIFT_MONITOR.get("score_inflation_tolerance", 15)
    
    # Check discrimination (item-total correlation)
    discrimination_low = item_total_correlation < DRIFT_MONITOR.get("low_discrimination_threshold", 0.20)
    
    # Fairness drift (DIF across subgroups)
    subgroup_drift_max = 0.0
    if subgroup_metrics:
        baseline_subgroup = monitoring_data.get("baseline_subgroup_metrics", {})
        for subgroup, current_metrics in subgroup_metrics.items():
            baseline = baseline_subgroup.get(subgroup, {})
            for metric_name, value in current_metrics.items():
                baseline_value = baseline.get(metric_name, 0.0)
                drift = abs(value - baseline_value)
                if drift > subgroup_drift_max:
                    subgroup_drift_max = drift
    
    fairness_drifted = subgroup_drift_max > DRIFT_MONITOR.get("fairness_drift_tolerance", 2.0)
    
    # Determine alert threshold
    alert_threshold = DRIFT_MONITOR.get("alert_threshold", 1.5)
    alert_triggered = (
        (difficulty_z_score > alert_threshold or fairness_drifted or inflation_flagged or discrimination_low)
    )
    
    alert_reasons = []
    if abs(difficulty_z_score) > alert_threshold:
        alert_reasons.append(f"Difficulty drift detected (z={difficulty_z_score:.2f})")
    if inflation_flagged:
        alert_reasons.append(f"Score inflation detected ({inflation_pct:.1f}%)")
    if fairness_drifted:
        alert_reasons.append(f"Fairness drift across subgroups ({subgroup_drift_max:.2f})")
    if discrimination_low:
        alert_reasons.append(f"Low discrimination (r={item_total_correlation:.2f})")
    
    # Recommend action
    if alert_triggered or abs(difficulty_z_score) > DRIFT_MONITOR.get("difficulty_drift_tolerance", 2.0):
        action_recommended = "retire"
    elif alert_triggered:
        action_recommended = "investigate"
    else:
        action_recommended = "monitor"
    
    result = DriftMonitoringResult(
        monitor_id=str(uuid.uuid4()),
        item_id=item_lifecycle.item_id,
        monitoring_period_days=monitoring_period_days,
        sample_size=sample_size,
        baseline_difficulty=baseline_difficulty,
        current_difficulty=current_difficulty,
        difficulty_z_score=difficulty_z_score,
        difficulty_drifted=difficulty_drifted,
        subgroup_drift_max=subgroup_drift_max,
        fairness_drifted=fairness_drifted,
        baseline_mean_score=baseline_mean_score,
        current_mean_score=current_mean_score,
        inflation_pct=inflation_pct,
        inflation_flagged=inflation_flagged,
        item_total_correlation=item_total_correlation,
        discrimination_low=discrimination_low,
        alert_triggered=alert_triggered,
        alert_reasons=alert_reasons,
        action_recommended=action_recommended,
        timestamp=datetime.utcnow(),
    )
    
    return result


def batch_drift_check(
    active_items: List[ItemLifecycle],
    monitoring_data_map: dict[str, dict],
) -> List[DriftMonitoringResult]:
    """
    Run drift check on multiple active items.
    
    Args:
        active_items: List of ItemLifecycle objects with status ACTIVE
        monitoring_data_map: Dict mapping item_id -> monitoring_data
    
    Returns:
        List of DriftMonitoringResults
    """
    
    results = []
    for item in active_items:
        if item.item_id in monitoring_data_map:
            result = run_monthly_drift_check(item, monitoring_data_map[item.item_id])
            results.append(result)
    
    return results


def identify_items_for_retirement(
    drift_results: List[DriftMonitoringResult],
    breach_count_threshold: int = 2,
) -> List[str]:
    """
    Identify items that should be auto-retired based on repeated drift breaches.
    
    Args:
        drift_results: List of DriftMonitoringResults
        breach_count_threshold: How many consecutive breaches before retiring
    
    Returns:
        List of item_ids to retire
    """
    
    # TODO: In production, query historical drift records to count consecutive breaches
    # For now, simple logic: if action_recommended is "retire", recommend retirement
    
    items_to_retire = [
        result.item_id
        for result in drift_results
        if result.action_recommended == "retire"
    ]
    
    return items_to_retire


__all__ = [
    "run_monthly_drift_check",
    "batch_drift_check",
    "identify_items_for_retirement",
]
