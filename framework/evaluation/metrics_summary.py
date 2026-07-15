"""
Metrics Summary Module.

Aggregates operational metrics during an experiment and provides utilities 
to mathematically compare two distinct experiment runs.
"""

from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass(slots=True)
class ExperimentMetrics:
    """Standardized metric container for experiment outcomes."""
    status: str = "UNKNOWN"
    execution_duration_sec: float = 0.0
    latency_ms: float = 0.0
    throughput_mbps: float = 0.0
    packet_counts: Dict[str, int] = field(default_factory=dict)
    interface_stats: Dict[str, Dict[str, int]] = field(default_factory=dict)


class MetricsComparator:
    """Provides statistical comparison between two sets of experiment metrics."""

    @staticmethod
    def compare(baseline: ExperimentMetrics, evaluation: ExperimentMetrics) -> Dict[str, Any]:
        """
        Compares two experiment runs and calculates deltas.
        
        Args:
            baseline: The control or previous experiment metrics.
            evaluation: The current experiment metrics to evaluate.
            
        Returns:
            A dictionary containing absolute and percentage differences.
        """
        def delta(base_val: float, eval_val: float) -> float:
            return eval_val - base_val
            
        def percent_change(base_val: float, eval_val: float) -> float:
            if base_val == 0:
                return 0.0
            return ((eval_val - base_val) / base_val) * 100.0

        return {
            "duration_delta_sec": delta(baseline.execution_duration_sec, evaluation.execution_duration_sec),
            "latency_delta_ms": delta(baseline.latency_ms, evaluation.latency_ms),
            "latency_percent_change": percent_change(baseline.latency_ms, evaluation.latency_ms),
            "throughput_delta_mbps": delta(baseline.throughput_mbps, evaluation.throughput_mbps),
            "status_transition": f"{baseline.status} -> {evaluation.status}"
        }