"""
Unit tests for the VPN Configuration layer.
"""

import pytest
from pathlib import Path
from lab.vpn.config import (
    VPNConfiguration,
    VPNProtocol,
    VPNRole,
    VPNConfigurationError,
    VPNInvalidCIDRError,
    VPNPeerResolutionError,
    VPNUnsupportedProtocolError,
    VPNInvalidEndpointError
)

VALID_YAML = """
name: "test_vpn"
protocol: "wireguard"
nodes:
  - namespace: "vpn_server"
    role: "server"
    interface:
      name: "wg0"
      address: "10.7.0.1/24"
      listen_port: 51820
    peers:
      - target_namespace: "client"
        allowed_ips:
          - "10.7.0.2/32"

  - namespace: "client"
    role: "client"
    interface:
      name: "wg0"
      address: "10.7.0.2/24"
    peers:
      - target_namespace: "vpn_server"
        endpoint: "192.168.1.100:51820"
        allowed_ips:
          - "0.0.0.0/0"
"""

@pytest.fixture
def temp_config_file(tmp_path: Path) -> Path:
    config_path = tmp_path / "wireguard.yaml"
    config_path.write_text(VALID_YAML)
    return config_path


def test_valid_configuration(temp_config_file: Path) -> None:
    """Verifies a correct VPN YAML is parsed into the expected models."""
    config = VPNConfiguration.load(temp_config_file)
    
    assert config.name == "test_vpn"
    assert config.protocol == VPNProtocol.WIREGUARD
    assert len(config.nodes) == 2
    
    server_node = next(n for n in config.nodes if n.role == VPNRole.SERVER)
    assert server_node.namespace == "vpn_server"
    assert server_node.interface.address == "10.7.0.1/24"
    assert server_node.interface.listen_port == 51820
    assert len(server_node.peers) == 1
    assert server_node.peers[0].allowed_ips == ["10.7.0.2/32"]


def test_invalid_protocol(tmp_path: Path) -> None:
    """Verifies unsupported protocols raise an error."""
    bad_yaml = VALID_YAML.replace('protocol: "wireguard"', 'protocol: "pptp"')
    p = tmp_path / "bad.yaml"
    p.write_text(bad_yaml)
    
    with pytest.raises(VPNUnsupportedProtocolError):
        VPNConfiguration.load(p)


def test_invalid_interface_cidr(tmp_path: Path) -> None:
    """Verifies malformed interface addresses are caught."""
    bad_yaml = VALID_YAML.replace("10.7.0.1/24", "999.999.999.999/24")
    p = tmp_path / "bad.yaml"
    p.write_text(bad_yaml)
    
    with pytest.raises(VPNInvalidCIDRError):
        VPNConfiguration.load(p)


def test_invalid_allowed_ips_cidr(tmp_path: Path) -> None:
    """Verifies malformed allowed_ips addresses are caught."""
    bad_yaml = VALID_YAML.replace("10.7.0.2/32", "10.7.0.x/32")
    p = tmp_path / "bad.yaml"
    p.write_text(bad_yaml)
    
    with pytest.raises(VPNInvalidCIDRError):
        VPNConfiguration.load(p)


def test_invalid_endpoint(tmp_path: Path) -> None:
    """Verifies malformed endpoints (missing port or bad IP) are caught."""
    bad_yaml = VALID_YAML.replace("192.168.1.100:51820", "192.168.1.100")  # Missing port
    p = tmp_path / "bad.yaml"
    p.write_text(bad_yaml)
    
    with pytest.raises(VPNInvalidEndpointError):
        VPNConfiguration.load(p)


def test_peer_resolution_error(tmp_path: Path) -> None:
    """Verifies peers must reference existing nodes in the configuration."""
    bad_yaml = VALID_YAML.replace('target_namespace: "client"', 'target_namespace: "ghost_namespace"')
    p = tmp_path / "bad.yaml"
    p.write_text(bad_yaml)
    
    with pytest.raises(VPNPeerResolutionError):
        VPNConfiguration.load(p)