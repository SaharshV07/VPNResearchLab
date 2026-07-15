"""
Unit tests for the Experiment Evaluation Harness.
"""

import json
from pathlib import Path
from framework.evaluation.experiment_registry import ExperimentRegistry
from framework.evaluation.metrics_summary import ExperimentMetrics, MetricsComparator
from framework.evaluation.report_builder import ReportBuilder


def test_experiment_registry_hashing(tmp_path: Path) -> None:
    """Verifies config files produce deterministic, unique SHA256 hashes."""
    cfg1 = tmp_path / "cfg1.yaml"
    cfg1.write_text("dummy_data: true")
    
    record = ExperimentRegistry.register("test_exp", "1.0", [cfg1])
    
    assert record.experiment_id == "test_exp"
    assert record.version == "1.0"
    assert len(record.config_hash) == 64  # SHA256 length
    assert "Python" in record.python_version


def test_metrics_comparator() -> None:
    """Verifies that mathematical comparison between two metric sets works properly."""
    baseline = ExperimentMetrics(
        status="SUCCESS",
        execution_duration_sec=10.0,
        latency_ms=5.0,
        throughput_mbps=100.0
    )
    
    evaluation = ExperimentMetrics(
        status="FAILED",
        execution_duration_sec=15.0,
        latency_ms=10.0,
        throughput_mbps=50.0
    )
    
    deltas = MetricsComparator.compare(baseline, evaluation)
    
    assert deltas["duration_delta_sec"] == 5.0
    assert deltas["latency_delta_ms"] == 5.0
    assert deltas["latency_percent_change"] == 100.0
    assert deltas["throughput_delta_mbps"] == -50.0
    assert deltas["status_transition"] == "SUCCESS -> FAILED"


def test_report_builder_generation(tmp_path: Path) -> None:
    """Verifies JSON and Markdown reports compile successfully from primitives."""
    record = ExperimentRegistry.register("test_exp", "v1", [])
    metrics = ExperimentMetrics(status="SUCCESS", execution_duration_sec=2.5, packet_counts={"eth0": 500})
    val_summary = {"Config Check": True, "VPN Active": True}
    
    builder = ReportBuilder(record, metrics, val_summary, tmp_path)
    
    json_path = builder.generate_json()
    md_path = builder.generate_markdown()
    
    assert json_path.exists()
    assert md_path.exists()
    
    with open(json_path, "r") as f:
        data = json.load(f)
        assert data["metadata"]["experiment_id"] == "test_exp"
        assert data["validation"]["VPN Active"] is True
        assert data["metrics"]["status"] == "SUCCESS"
        assert data["metrics"]["packet_counts"]["eth0"] == 500