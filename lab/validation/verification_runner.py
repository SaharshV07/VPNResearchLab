"""
Verification Runner Module.

Orchestrates a comprehensive suite of checks across namespaces, interfaces, 
VPN state, routing, NAT, and connectivity to prove lab integrity.
"""

import logging
from typing import Dict, Any, List
import datetime

from lab.config import LabConfiguration
from lab.vpn.config import VPNConfiguration, VPNRole
from lab.topology.namespace_manager import NamespaceManager
from lab.validation.metrics_collector import MetricsCollector

logger = logging.getLogger(__name__)


class VerificationSuite:
    """Executes the baseline environment verification checks."""

    def __init__(self, lab_config: LabConfiguration, vpn_config: VPNConfiguration, ns_manager: NamespaceManager):
        self.lab = lab_config
        self.vpn = vpn_config
        self.ns = ns_manager
        self.metrics = MetricsCollector(ns_manager)
        
        self.results: Dict[str, Any] = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "environment_name": self.lab.lab_name,
            "checks": {},
            "metrics": {}
        }

    def _get_app_server_ip(self) -> str:
        for ns in self.lab.namespaces:
            if ns.name == "app_server":
                return ns.interfaces[0].ip.split('/')[0]
        return ""

    def run_all(self) -> Dict[str, Any]:
        """Runs the entire verification suite and returns the structured results."""
        logger.info("=== Starting Environment Verification ===")
        self.results["checks"]["namespaces"] = self._verify_namespaces()
        self.results["checks"]["interfaces"] = self._verify_interfaces()
        self.results["checks"]["wireguard"] = self._verify_wireguard()
        self.results["checks"]["routing"] = self._verify_routing()
        self.results["checks"]["nat"] = self._verify_nat()
        self.results["checks"]["connectivity"] = self._verify_connectivity()
        
        logger.info("=== Collecting Baseline Metrics ===")
        self.results["metrics"] = self._collect_metrics()
        
        return self.results

    def _verify_namespaces(self) -> Dict[str, bool]:
        checks = {}
        for ns in self.lab.namespaces:
            checks[ns.name] = self.ns.namespace_exists(ns.name)
        return checks

    def _verify_interfaces(self) -> Dict[str, bool]:
        checks = {}
        for ns in self.lab.namespaces:
            for iface in ns.interfaces:
                out = self.ns.execute(ns.name, ["ip", "link", "show", iface.name])
                checks[f"{ns.name}:{iface.name}"] = "UP" in out.split(",")[0]
        return checks

    def _verify_wireguard(self) -> Dict[str, bool]:
        checks = {}
        for node in self.vpn.nodes:
            try:
                out = self.ns.execute(node.namespace, ["wg", "show", node.interface.name])
                # Check if wg interface is active and has a public key configured
                checks[f"{node.namespace}:wg0_active"] = "public key:" in out
                
                # Check for handshakes if there are peers
                if node.peers:
                    hs_out = self.ns.execute(node.namespace, ["wg", "show", node.interface.name, "latest-handshakes"])
                    checks[f"{node.namespace}:handshake"] = bool(hs_out.strip() and "0" not in hs_out.split("\t")[1])
            except Exception:
                checks[f"{node.namespace}:wg0_active"] = False
        return checks

    def _verify_routing(self) -> Dict[str, bool]:
        checks = {}
        # Client MUST route all traffic to wg0
        try:
            out = self.ns.execute("client", ["ip", "route", "show"])
            checks["client_default_route_wg0"] = "default dev wg0" in out
        except Exception:
            checks["client_default_route_wg0"] = False

        # VPN Server must forward traffic
        try:
            fwd = self.ns.execute("vpn_server", ["sysctl", "-n", "net.ipv4.ip_forward"])
            checks["vpn_server_forwarding"] = fwd.strip() == "1"
        except Exception:
            checks["vpn_server_forwarding"] = False
            
        return checks

    def _verify_nat(self) -> Dict[str, bool]:
        checks = {}
        try:
            out = self.ns.execute("vpn_server", ["iptables", "-t", "nat", "-S"])
            # The MASQUERADE rule for the VPN subnet MUST exist
            checks["vpn_server_masquerade"] = "-A POSTROUTING -s 10.7.0.0/24 -j MASQUERADE" in out
        except Exception:
            checks["vpn_server_masquerade"] = False
        return checks

    def _verify_connectivity(self) -> Dict[str, bool]:
        checks = {}
        app_ip = self._get_app_server_ip()
        
        rtt = self.metrics.measure_rtt(app_ip)
        checks["end_to_end_icmp"] = rtt > 0

        # Verify HTTP Application Traffic
        try:
            out = self.ns.execute("client", ["python3", "-c", f"import urllib.request; print(urllib.request.urlopen('http://{app_ip}:8000', timeout=2).read().decode())"])
            checks["end_to_end_http"] = "HTTP_PAYLOAD_OK" in out
        except Exception:
            checks["end_to_end_http"] = False

        return checks

    def _collect_metrics(self) -> Dict[str, Any]:
        app_ip = self._get_app_server_ip()
        metrics: Dict[str, Any] = {}
        
        metrics["rtt_ms"] = self.metrics.measure_rtt(app_ip)
        metrics["throughput_mbps"] = self.metrics.measure_throughput_mbps(app_ip)
        
        # Interface stats for the tunnel endpoints
        metrics["interface_stats"] = {
            "client_wg0": self.metrics.get_interface_statistics("client", "wg0").__dict__,
            "vpn_server_wg0": self.metrics.get_interface_statistics("vpn_server", "wg0").__dict__,
            "gateway_g-eth0": self.metrics.get_interface_statistics("gateway", "g-eth0").__dict__
        }
        
        return metrics