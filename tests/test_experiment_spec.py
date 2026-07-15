"""
Unit tests for the Experiment Specification Layer.
"""

import pytest
from pathlib import Path

from framework.evaluation.environment_requirements import EnvironmentRequirements
from framework.evaluation.artifact_manifest import ArtifactManifest, ArtifactValidator
from framework.evaluation.experiment_spec import ExperimentSpecification


@pytest.fixture
def sample_spec() -> ExperimentSpecification:
    """Provides a valid, populated ExperimentSpecification for testing."""
    env = EnvironmentRequirements(
        namespaces=["client", "gateway", "vpn_server"],
        vpn_required=True,
        required_services=["http:8000"],
        required_interfaces=["wg0", "g-eth0"],
        config_versions={"topology": "1.0", "vpn": "1.0"}
    )
    
    manifest = ArtifactManifest(
        json_report="report.json",
        md_report="report.md",
        metrics_summary="metrics.sqlite3",
        log_files=["runtime.log"],
        pcap_files=["capture.pcap"]
    )
    
    return ExperimentSpecification(
        experiment_id="exp_01_test",
        version="1.0.0",
        objective="Verify virtual IP inference baseline conditions.",
        required_config_files=[Path("configs/topology.yaml")],
        environment=env,
        expected_manifest=manifest,
        validation_criteria={"success_rate": 1.0}
    )


def test_specification_metadata_validation(sample_spec: ExperimentSpecification) -> None:
    """Verifies that a well-formed specification passes metadata checks."""
    sample_spec.validate_metadata()  # Should not raise


def test_specification_metadata_validation_fails() -> None:
    """Verifies that missing critical metadata raises an error."""
    bad_spec = ExperimentSpecification(
        experiment_id="", # Invalid
        version="1.0",
        objective="Testing failure",
        required_config_files=[Path("fake.yaml")],
        environment=EnvironmentRequirements(),
        expected_manifest=ArtifactManifest("j", "m", "s")
    )
    
    with pytest.raises(ValueError, match="requires a valid 'experiment_id'"):
        bad_spec.validate_metadata()


def test_environment_config_version_validation(sample_spec: ExperimentSpecification) -> None:
    """Verifies that version mismatches in configuration are caught."""
    active_versions = {"topology": "1.0", "vpn": "1.0"}
    sample_spec.environment.validate_config_versions(active_versions) # Should pass
    
    bad_versions = {"topology": "1.0", "vpn": "0.9"}
    with pytest.raises(ValueError, match="Configuration version mismatch"):
        sample_spec.environment.validate_config_versions(bad_versions)


def test_artifact_validator(sample_spec: ExperimentSpecification, tmp_path: Path) -> None:
    """Verifies the artifact manifest correctly checks the filesystem."""
    # Create the fake expected files
    (tmp_path / "report.json").touch()
    (tmp_path / "report.md").touch()
    (tmp_path / "metrics.sqlite3").touch()
    (tmp_path / "runtime.log").touch()
    (tmp_path / "capture.pcap").touch()
    
    assert ArtifactValidator.validate(sample_spec.expected_manifest, tmp_path) is True


def test_artifact_validator_missing_file(sample_spec: ExperimentSpecification, tmp_path: Path) -> None:
    """Verifies the artifact manifest fails when expected files are absent."""
    (tmp_path / "report.json").touch()
    # Intentionally missing the rest...
    
    with pytest.raises(FileNotFoundError, match="Experiment failed to produce 4 required artifacts"):
        ArtifactValidator.validate(sample_spec.expected_manifest, tmp_path)