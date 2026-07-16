"""
Unit tests for the Baseline Validation Execution workflow.
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from experiments.run_baseline_validation import BaselineValidationExperiment, create_baseline_specification
from framework.evaluation.experiment_spec import ExperimentSpecification


@pytest.fixture
def mock_spec(tmp_path: Path) -> ExperimentSpecification:
    """Provides a valid baseline specification."""
    # Touch fake config files to pass basic path checks
    cfg_dir = tmp_path / "configs"
    cfg_dir.mkdir()
    (cfg_dir / "topology.yaml").touch()
    (cfg_dir / "wireguard.yaml").touch()
    
    return create_baseline_specification(tmp_path)


@patch("experiments.run_baseline_validation.ArtifactValidator.validate")
@patch("experiments.run_baseline_validation.ReportBuilder")
@patch("experiments.run_baseline_validation.ExperimentRegistry.register")
@patch("experiments.run_baseline_validation.MetricsCollector")
@patch("experiments.run_baseline_validation.TrafficGenerator")
@patch("experiments.run_baseline_validation.CapturePipeline")
@patch("experiments.run_baseline_validation.EvaluationValidator")
@patch("experiments.experiment_runtime.BaseExperiment.initialize")
def test_baseline_experiment_flow(
    mock_base_init: MagicMock,
    mock_eval: MagicMock,
    mock_capture: MagicMock,
    mock_traffic: MagicMock,
    mock_metrics: MagicMock,
    mock_registry: MagicMock,
    mock_builder: MagicMock,
    mock_artifact_val: MagicMock,
    mock_spec: ExperimentSpecification,
    tmp_path: Path
) -> None:
    """
    Verifies that the BaselineValidationExperiment overrides correctly call 
    the underlying Evaluation, Observation, and Traffic frameworks in order.
    """
    # Setup mocks
    mock_eval_instance = mock_eval.return_value
    mock_traffic_instance = mock_traffic.return_value
    mock_traffic_instance.generate_http.return_value = (True, "HTTP_PAYLOAD_OK")
    
    mock_metrics_instance = mock_metrics.return_value
    mock_metrics_instance.measure_rtt.return_value = 1.25
    mock_metrics_instance.measure_throughput_mbps.return_value = 100.0
    from types import SimpleNamespace   
    mock_metrics_instance.get_interface_statistics.return_value = SimpleNamespace(
    rx_bytes=100
    )
    
    # Initialize Experiment
    experiment = BaselineValidationExperiment(spec=mock_spec, base_dir=tmp_path)
    

    experiment.lab_config = MagicMock()
    experiment.vpn_config = MagicMock()
    experiment.ns_manager = MagicMock()
    experiment.cleanup_manager = MagicMock()
    experiment.logger = MagicMock()
    # Test initialize()
    experiment.initialize()
    mock_base_init.assert_called_once()
    mock_eval_instance.run_pre_flight_checks.assert_called_once_with(mock_spec.required_config_files)
    
    # Test execute_experiment()
    # Stubbing internal helpers that require real config parsing
    experiment._get_app_server_ip = MagicMock(return_value="172.16.1.10")
    experiment.ns_manager = MagicMock()
    experiment.cleanup_manager = MagicMock()
    
    experiment.execute_experiment()
    mock_capture.assert_called_once()
    mock_traffic_instance.generate_http.assert_called_once_with("172.16.1.10", 8000)
    assert experiment.metrics.status == "SUCCESS"
    
    # Test collect_results()
    experiment.collect_results()
    assert experiment.metrics.latency_ms == 1.25
    assert experiment.metrics.throughput_mbps == 100.0
    
    # Test generate_report()
    experiment.generate_report()
    mock_registry.assert_called_once()
    mock_builder.assert_called_once()
    mock_artifact_val.assert_called_once_with(mock_spec.expected_manifest, experiment.artifact_dir)