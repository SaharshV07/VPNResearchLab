"""
Unit tests for the Configuration parser and validator.
"""

import pytest
import yaml
from pathlib import Path
from lab.config import (
    LabConfiguration,
    ConfigurationError,
    DuplicateNamespaceError,
    DuplicateInterfaceError,
    InvalidCIDRError,
    InvalidIPError,
    MissingGatewayError,
    TopologyConsistencyError
)

# A minimal valid configuration block for testing
VALID_YAML = """
lab_name: "test_lab"
description: "Test description"
subnets:
  - "10.0.0.0/24"
namespaces:
  - name: "client"
    forwarding: false
    interfaces:
      - name: "eth0"
        type: "veth"
        ip: "10.0.0.10/24"
    routes:
      - target: "0.0.0.0/0"
        gateway: "10.0.0.1"
"""

@pytest.fixture
def temp_config_file(tmp_path: Path) -> Path:
    config_path = tmp_path / "topology.yaml"
    config_path.write_text(VALID_YAML)
    return config_path


def test_valid_configuration(temp_config_file: Path) -> None:
    """Verifies a correctly formed YAML loads without errors."""
    config = LabConfiguration.load(temp_config_file)
    assert config.lab_name == "test_lab"
    assert len(config.namespaces) == 1
    assert config.namespaces[0].name == "client"


def test_duplicate_namespace(tmp_path: Path) -> None:
    """Verifies duplicate namespace names raise DuplicateNamespaceError."""
    bad_yaml = VALID_YAML + """
  - name: "client"
    forwarding: true
"""
    p = tmp_path / "bad.yaml"
    p.write_text(bad_yaml)
    with pytest.raises(DuplicateNamespaceError):
        LabConfiguration.load(p)


def test_duplicate_interface(tmp_path: Path) -> None:
    """Verifies duplicate interface names globally raise DuplicateInterfaceError."""
    bad_yaml = VALID_YAML + """
  - name: "router"
    forwarding: true
    interfaces:
      - name: "eth0"
        type: "veth"
"""
    p = tmp_path / "bad.yaml"
    p.write_text(bad_yaml)
    with pytest.raises(DuplicateInterfaceError):
        LabConfiguration.load(p)


def test_invalid_subnet_cidr(tmp_path: Path) -> None:
    """Verifies malformed subnets raise InvalidCIDRError."""
    bad_yaml = VALID_YAML.replace("10.0.0.0/24", "10.0.0.999/24")
    p = tmp_path / "bad.yaml"
    p.write_text(bad_yaml)
    with pytest.raises(InvalidCIDRError):
        LabConfiguration.load(p)


def test_invalid_interface_ip(tmp_path: Path) -> None:
    """Verifies malformed IPs on interfaces raise InvalidIPError."""
    bad_yaml = VALID_YAML.replace("10.0.0.10/24", "999.999.999.999/24")
    p = tmp_path / "bad.yaml"
    p.write_text(bad_yaml)
    with pytest.raises(InvalidIPError):
        LabConfiguration.load(p)


def test_missing_gateway(tmp_path: Path) -> None:
    """Verifies a route without a gateway or device throws MissingGatewayError."""
    bad_yaml = VALID_YAML.replace('gateway: "10.0.0.1"', "")
    p = tmp_path / "bad.yaml"
    p.write_text(bad_yaml)
    with pytest.raises(MissingGatewayError):
        LabConfiguration.load(p)


def test_topology_consistency(tmp_path: Path) -> None:
    """Verifies referencing non-existent namespaces raises TopologyConsistencyError."""
    bad_yaml = VALID_YAML.replace('type: "veth"', 'type: "veth"\n        peer_namespace: "ghost"')
    p = tmp_path / "bad.yaml"
    p.write_text(bad_yaml)
    with pytest.raises(TopologyConsistencyError):
        LabConfiguration.load(p)


def test_malformed_yaml(tmp_path: Path) -> None:
    """Verifies fundamentally broken YAML raises ConfigurationError."""
    p = tmp_path / "bad.yaml"
    p.write_text("lab_name: [unclosed_bracket")
    with pytest.raises(ConfigurationError):
        LabConfiguration.load(p)