"""
Integration tests for the VPN Deployment sequence.
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from lab.vpn.config import VPNConfiguration
from lab.topology.namespace_manager import NamespaceManager, LabConfig
from lab.vpn.vpn_manager import VPNManager
from lab.vpn.validator import VPNValidator, ValidationResult

VALID_YAML = """
name: "test_vpn"
protocol: "wireguard"
nodes:
  - namespace: "vpn_server"
    role: "server"
    interface:
      name: "wg0"
      address: "10.7.0.1/24"
    peers: []
    routes: []
  - namespace: "client"
    role: "client"
    interface:
      name: "wg0"
      address: "10.7.0.2/24"
    peers: []
    routes: []
"""

@pytest.fixture
def mock_config(tmp_path: Path) -> VPNConfiguration:
    p = tmp_path / "wg.yaml"
    p.write_text(VALID_YAML)
    return VPNConfiguration.load(p)


@patch("lab.vpn.key_manager.subprocess.run")
@patch("lab.topology.namespace_manager.subprocess.run")
def test_vpn_manager_deploy(mock_ns_run: MagicMock, mock_key_run: MagicMock, mock_config: VPNConfiguration) -> None:
    """Verifies that the VPN deployment properly orchestrates interface and NAT commands."""
    mock_ns_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
    mock_key_run.return_value = MagicMock(returncode=0, stdout="dummy_key\n", stderr="")
    
    ns_manager = NamespaceManager(LabConfig(namespaces=["client", "vpn_server"]))
    vpn_manager = VPNManager(mock_config, ns_manager)
    
    vpn_manager.deploy()
    
    # Assert NAT MASQUERADE was invoked on the server
    mock_ns_run.assert_any_call(
        ["ip", "netns", "exec", "vpn_server", "iptables", "-t", "nat", "-A", "POSTROUTING", "-s", "10.7.0.0/24", "-j", "MASQUERADE"],
        capture_output=True, text=True, check=False
    )
    # Assert Weak Host Model (rp_filter) was invoked on the client
    mock_ns_run.assert_any_call(
        ["ip", "netns", "exec", "client", "sysctl", "-w", "net.ipv4.conf.all.rp_filter=2"],
        capture_output=True, text=True, check=False
    )


@patch("lab.topology.namespace_manager.NamespaceManager.execute")
@patch("lab.topology.namespace_manager.NamespaceManager.namespace_exists")
def test_vpn_validator_success(mock_exists: MagicMock, mock_exec: MagicMock, mock_config: VPNConfiguration) -> None:
    """Verifies the validator parses successful kernel states correctly."""
    mock_exists.return_value = True
    
    def execute_side_effect(ns, cmd):
        cmd_str = " ".join(cmd)
        if "link show" in cmd_str: return "UP,LOWER_UP"
        if "sysctl -n net.ipv4.conf.all.rp_filter" in cmd_str: return "2"
        if "iptables -t nat -S" in cmd_str: return "-A POSTROUTING -s 10.7.0.0/24 -j MASQUERADE"
        if "latest-handshakes" in cmd_str: return "peer_key\t1600000000"
        if "ping" in cmd_str: return "time=1.45 ms"
        if "urllib" in cmd_str: return "HTTP_PAYLOAD_OK"
        if "socket" in cmd_str: return "120.5" # throughput
        return ""
        
    mock_exec.side_effect = execute_side_effect
    
    ns_manager = NamespaceManager(LabConfig(namespaces=["client", "vpn_server"]))
    validator = VPNValidator(mock_config, ns_manager)
    result = validator.validate("1.1.1.1")
    
    assert result.namespaces is True
    assert result.interfaces is True
    assert result.nat is True
    assert result.routing is True
    assert result.handshake is True
    assert result.connectivity is True
    assert result.rtt_ms == 1.45
    assert result.throughput_mbps == 120.5