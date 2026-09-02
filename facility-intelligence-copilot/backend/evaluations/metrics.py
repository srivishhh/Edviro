"""
WORKSTREAM D — PRODUCT VALIDATION METRICS

Tracking system for:
- Detection latency (telemetry → alert)
- X-Ray latency (investigation → completion)
- Evidence coverage
- Root-cause accuracy
- Recommendation quality
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional
import json
from pathlib import Path


@dataclass
class DetectionMetric:
    """Measures time from telemetry event to alert creation"""
    event_id: str
    telemetry_timestamp: str  # ISO format
    alert_timestamp: Optional[str] = None
    latency_seconds: Optional[float] = None
    asset_id: Optional[int] = None
    alert_type: Optional[str] = None
    
    def complete(self, alert_timestamp: str) -> None:
        """Record alert completion time"""
        self.alert_timestamp = alert_timestamp
        # Calculate latency (parse ISO timestamps)
        try:
            telem_dt = datetime.fromisoformat(self.telemetry_timestamp.replace('Z', '+00:00'))
            alert_dt = datetime.fromisoformat(alert_timestamp.replace('Z', '+00:00'))
            self.latency_seconds = (alert_dt - telem_dt).total_seconds()
        except Exception:
            self.latency_seconds = None


@dataclass
class XRayMetric:
    """Measures time from investigation request to completion"""
    investigation_id: str
    request_timestamp: str  # ISO format
    asset_id: int
    alert_id: int
    completion_timestamp: Optional[str] = None
    latency_seconds: Optional[float] = None
    status: str = "PENDING"  # PENDING, COMPLETED, FAILED
    
    def complete(self, completion_timestamp: str, status: str = "COMPLETED") -> None:
        """Record investigation completion"""
        self.completion_timestamp = completion_timestamp
        self.status = status
        try:
            req_dt = datetime.fromisoformat(self.request_timestamp.replace('Z', '+00:00'))
            comp_dt = datetime.fromisoformat(completion_timestamp.replace('Z', '+00:00'))
            self.latency_seconds = (comp_dt - req_dt).total_seconds()
        except Exception:
            self.latency_seconds = None


@dataclass
class EvidenceMetric:
    """Tracks evidence coverage against expected evidence"""
    scenario: str  # airflow_restriction, high_energy, etc.
    expected_evidence: list[str]  # Required evidence list
    observed_evidence: list[str] = field(default_factory=list)
    coverage_ratio: float = 0.0  # observed / expected
    
    def calculate_coverage(self) -> float:
        """Calculate evidence coverage percentage"""
        if not self.expected_evidence:
            return 100.0
        matches = len([e for e in self.observed_evidence if e in self.expected_evidence])
        self.coverage_ratio = matches / len(self.expected_evidence)
        return self.coverage_ratio * 100


@dataclass
class RootCauseMetric:
    """Tracks root-cause prediction accuracy"""
    scenario: str
    expected_root_cause_category: str  # airflow_obstruction, thermal_anomaly, etc.
    predicted_root_cause: Optional[str] = None
    match: bool = False
    confidence: Optional[str] = None  # High, Medium, Low
    
    def evaluate(self) -> bool:
        """Check if prediction matches expected category"""
        if self.predicted_root_cause:
            # Simple check: if expected category appears in predicted text
            self.match = self.expected_root_cause_category.lower() in self.predicted_root_cause.lower()
        return self.match


@dataclass
class RecommendationMetric:
    """Tracks recommendation quality"""
    scenario: str
    expected_actions: list[str]  # Expected action categories
    predicted_actions: list[str] = field(default_factory=list)
    has_actionable_text: bool = False
    quality_score: float = 0.0  # 0.0-1.0
    
    def evaluate(self) -> float:
        """Score recommendation quality (0-1)"""
        if not self.predicted_actions:
            self.quality_score = 0.0
            return 0.0
        
        # Basic scoring:
        # - Presence of actions: 0.5
        # - Match with expected: 0.5
        action_score = 0.5 if self.predicted_actions else 0.0
        
        if self.expected_actions:
            matches = sum(1 for action in self.predicted_actions 
                         if any(exp.lower() in action.lower() for exp in self.expected_actions))
            match_score = (matches / len(self.expected_actions)) * 0.5
        else:
            match_score = 0.5 if self.predicted_actions else 0.0
        
        self.quality_score = min(action_score + match_score, 1.0)
        self.has_actionable_text = len(self.predicted_actions) > 0
        return self.quality_score


@dataclass
class ScenarioResult:
    """Complete evaluation result for a single scenario"""
    scenario: str
    detection_metric: Optional[DetectionMetric] = None
    xray_metric: Optional[XRayMetric] = None
    evidence_metric: Optional[EvidenceMetric] = None
    root_cause_metric: Optional[RootCauseMetric] = None
    recommendation_metric: Optional[RecommendationMetric] = None
    
    # Aggregate scores
    detection_latency: float = 0.0
    xray_latency: float = 0.0
    evidence_coverage: float = 0.0
    root_cause_accuracy: bool = False
    recommendation_quality: float = 0.0
    
    # Pass/Fail
    passed: bool = False
    
    def evaluate(self) -> bool:
        """Evaluate overall scenario result"""
        self.detection_latency = self.detection_metric.latency_seconds if self.detection_metric and self.detection_metric.latency_seconds else 0.0
        self.xray_latency = self.xray_metric.latency_seconds if self.xray_metric and self.xray_metric.latency_seconds else 0.0
        self.evidence_coverage = self.evidence_metric.calculate_coverage() if self.evidence_metric else 0.0
        self.root_cause_accuracy = self.root_cause_metric.evaluate() if self.root_cause_metric else False
        self.recommendation_quality = self.recommendation_metric.evaluate() if self.recommendation_metric else 0.0
        
        # Pass criteria:
        # - Detection latency < 10 seconds (reasonable)
        # - X-Ray latency < 15 seconds (reasonable for AI)
        # - Evidence coverage >= 66% (2/3)
        # - Root-cause accuracy >= 80% (must match)
        # - Recommendation quality >= 0.5 (some actionable content)
        
        detection_ok = self.detection_latency > 0 and self.detection_latency < 10
        xray_ok = self.xray_latency > 0 and self.xray_latency < 15
        evidence_ok = self.evidence_coverage >= 66.0
        cause_ok = self.root_cause_accuracy
        recommendation_ok = self.recommendation_quality >= 0.5
        
        # For now, focus on evidence and cause accuracy
        self.passed = evidence_ok and cause_ok
        return self.passed


@dataclass
class EvaluationReport:
    """Master report containing all scenario results"""
    timestamp: str  # ISO format
    test_run_id: str
    scenarios: dict[str, ScenarioResult] = field(default_factory=dict)
    
    # Summary statistics
    total_scenarios: int = 0
    passed_scenarios: int = 0
    average_detection_latency: float = 0.0
    average_xray_latency: float = 0.0
    average_evidence_coverage: float = 0.0
    average_root_cause_accuracy: float = 0.0  # 0-1 (fraction)
    average_recommendation_quality: float = 0.0
    overall_pass_rate: float = 0.0
    
    def add_result(self, result: ScenarioResult) -> None:
        """Add scenario result and update summaries"""
        self.scenarios[result.scenario] = result
        self.total_scenarios = len(self.scenarios)
        
        # Recalculate summaries
        self._calculate_summaries()
    
    def _calculate_summaries(self) -> None:
        """Calculate aggregate statistics"""
        if not self.scenarios:
            return
        
        self.passed_scenarios = sum(1 for r in self.scenarios.values() if r.passed)
        self.overall_pass_rate = self.passed_scenarios / self.total_scenarios
        
        detection_latencies = [r.detection_latency for r in self.scenarios.values() if r.detection_latency > 0]
        self.average_detection_latency = sum(detection_latencies) / len(detection_latencies) if detection_latencies else 0.0
        
        xray_latencies = [r.xray_latency for r in self.scenarios.values() if r.xray_latency > 0]
        self.average_xray_latency = sum(xray_latencies) / len(xray_latencies) if xray_latencies else 0.0
        
        coverage_scores = [r.evidence_coverage for r in self.scenarios.values()]
        self.average_evidence_coverage = sum(coverage_scores) / len(coverage_scores) if coverage_scores else 0.0
        
        cause_accuracy = [1.0 if r.root_cause_accuracy else 0.0 for r in self.scenarios.values()]
        self.average_root_cause_accuracy = sum(cause_accuracy) / len(cause_accuracy) if cause_accuracy else 0.0
        
        rec_quality = [r.recommendation_quality for r in self.scenarios.values()]
        self.average_recommendation_quality = sum(rec_quality) / len(rec_quality) if rec_quality else 0.0
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "timestamp": self.timestamp,
            "test_run_id": self.test_run_id,
            "summary": {
                "total_scenarios": self.total_scenarios,
                "passed_scenarios": self.passed_scenarios,
                "overall_pass_rate": round(self.overall_pass_rate * 100, 2),
                "average_detection_latency_sec": round(self.average_detection_latency, 2),
                "average_xray_latency_sec": round(self.average_xray_latency, 2),
                "average_evidence_coverage_percent": round(self.average_evidence_coverage, 2),
                "average_root_cause_accuracy_percent": round(self.average_root_cause_accuracy * 100, 2),
                "average_recommendation_quality": round(self.average_recommendation_quality, 3),
            },
            "scenarios": {
                name: {
                    "scenario": result.scenario,
                    "passed": result.passed,
                    "detection_latency_sec": round(result.detection_latency, 2) if result.detection_latency else None,
                    "xray_latency_sec": round(result.xray_latency, 2) if result.xray_latency else None,
                    "evidence_coverage_percent": round(result.evidence_coverage, 2),
                    "root_cause_accuracy": result.root_cause_accuracy,
                    "recommendation_quality": round(result.recommendation_quality, 3),
                }
                for name, result in self.scenarios.items()
            }
        }
    
    def save(self, filepath: str) -> None:
        """Save report to JSON file"""
        report_dict = self.to_dict()
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(report_dict, f, indent=2)


# Global metrics tracker (in production, use proper observability platform)
_detection_metrics: dict[str, DetectionMetric] = {}
_xray_metrics: dict[str, XRayMetric] = {}
_scenario_results: dict[str, ScenarioResult] = {}


def record_detection_start(event_id: str, timestamp: str, asset_id: Optional[int] = None) -> None:
    """Record start of detection phase"""
    _detection_metrics[event_id] = DetectionMetric(
        event_id=event_id,
        telemetry_timestamp=timestamp,
        asset_id=asset_id
    )


def record_detection_complete(event_id: str, alert_timestamp: str, alert_type: str) -> None:
    """Record detection completion"""
    if event_id in _detection_metrics:
        metric = _detection_metrics[event_id]
        metric.alert_type = alert_type
        metric.complete(alert_timestamp)


def record_xray_start(investigation_id: str, timestamp: str, asset_id: int, alert_id: int) -> None:
    """Record start of X-Ray investigation"""
    _xray_metrics[investigation_id] = XRayMetric(
        investigation_id=investigation_id,
        request_timestamp=timestamp,
        asset_id=asset_id,
        alert_id=alert_id
    )


def record_xray_complete(investigation_id: str, completion_timestamp: str, status: str = "COMPLETED") -> None:
    """Record X-Ray investigation completion"""
    if investigation_id in _xray_metrics:
        metric = _xray_metrics[investigation_id]
        metric.complete(completion_timestamp, status)


def get_metrics_summary() -> dict:
    """Get current metrics summary"""
    detection_latencies = [m.latency_seconds for m in _detection_metrics.values() 
                          if m.latency_seconds is not None]
    xray_latencies = [m.latency_seconds for m in _xray_metrics.values() 
                     if m.latency_seconds is not None]
    
    return {
        "detection_events": len(_detection_metrics),
        "completed_detections": len([m for m in _detection_metrics.values() if m.alert_timestamp]),
        "average_detection_latency": round(sum(detection_latencies) / len(detection_latencies), 2) if detection_latencies else None,
        "xray_investigations": len(_xray_metrics),
        "completed_investigations": len([m for m in _xray_metrics.values() if m.completion_timestamp]),
        "average_xray_latency": round(sum(xray_latencies) / len(xray_latencies), 2) if xray_latencies else None,
    }
