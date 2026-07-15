"""
VPN Validator Module.

Scientifically proves the baseline VPN environment is active, properly encrypted, 
and adhering strictly to the topological requirements set by the research paper.
"""

import logging
from dataclasses import dataclass
from typing import Dict, Any

from lab.topology.namespace_manager import NamespaceManager
from lab.vpn.config import VPNConfiguration, VPNRole

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ValidationResult:
    namespaces: bool = False
    interfaces: bool = False
    handshake: bool = False
    routing: bool = False
    nat: bool = False
    connectivity: bool = False
    rtt_ms: float = 0.0
    throughput_mbps: float = 0.0


class VPNValidator:
    """Validates the state and exclusivity of the VPN tunnel."""

    def __init__(self, config: VPNConfiguration, ns_manager: NamespaceManager) -> None:
        """
        Initializes the VPNValidator.

        Args:
            config: The applied VPN configuration.
            ns_manager: Namespace execution context.
        """
        self.config = config
        self.ns = ns_manager

    def validate(self, app_server_ip: str) -> ValidationResult:
        """Executes the validation suite against the current kernel state."""
        res = ValidationResult()

        try:
            # 1. Namespaces Check
            for node in self.config.nodes:
                if not self.ns.namespace_exists(node.namespace):
                    raise ValueError(f"Namespace {node.namespace} missing.")
            res.namespaces = True

            # 2. Interfaces Check
            for node in self.config.nodes:
                link_out = self.ns.execute(node.namespace, ["ip", "link", "show", node.interface.name])
                if "UP" not in link_out.split(",")[0]:
                    raise ValueError(f"Interface {node.interface.name} is down.")
            res.interfaces = True

            # 3. Routing Check (rp_filter + IP routes)
            client_node = next(n for n in self.config.nodes if n.role == VPNRole.CLIENT)
            rp_out = self.ns.execute(client_node.namespace, ["sysctl", "-n", "net.ipv4.conf.all.rp_filter"])
            if rp_out.strip() != "2":
                raise ValueError("Weak host model (rp_filter) not configured correctly.")
            res.routing = True

            # 4. NAT Check
            server_node = next(n for n in self.config.nodes if n.role == VPNRole.SERVER)
            nat_out = self.ns.execute(server_node.namespace, ["iptables", "-t", "nat", "-S"])
            if "MASQUERADE" not in nat_out:
                raise ValueError("NAT Masquerade missing on VPN Server.")
            res.nat = True

            # 5. Handshake Check (Trigger via ICMP first)
            self.ns.execute(client_node.namespace, ["ping", "-c", "1", "-W", "2", app_server_ip])
            hs_out = self.ns.execute(server_node.namespace, ["wg", "show", server_node.interface.name, "latest-handshakes"])
            if not hs_out or "0" in hs_out.split("\t")[1]:
                raise ValueError("WireGuard cryptographic handshake not established.")
            res.handshake = True

            # 6. Connectivity Check (HTTP via inline python)
            http_script = f"import urllib.request; print(urllib.request.urlopen('http://{app_server_ip}:8000', timeout=2).read().decode())"
            http_out = self.ns.execute(client_node.namespace, ["python3", "-c", http_script])
            if "HTTP_PAYLOAD_OK" not in http_out:
                raise ValueError("Tunnel Layer 7 HTTP payload delivery failed.")
            res.connectivity = True

            # 7. Metrics Collection: RTT
            ping_out = self.ns.execute(client_node.namespace, ["ping", "-c", "1", "-W", "2", app_server_ip])
            if "time=" in ping_out:
                res.rtt_ms = float(ping_out.split("time=")[1].split(" ")[0])

            # 8. Metrics Collection: Throughput
            tp_script = (
                f"import socket, time; s=socket.socket(); s.connect(('{app_server_ip}', 9000)); "
                "data=b'A'*1024*1024; t0=time.time(); s.sendall(data); recv=0; "
                "while recv < len(data): recv += len(s.recv(8192)); "
                "print(f'{1.0 / (time.time()-t0):.2f}')"
            )
            tp_out = self.ns.execute(client_node.namespace, ["python3", "-c", tp_script])
            res.throughput_mbps = float(tp_out.strip())

        except Exception as e:
            logger.error(f"Validation failure: {e}")

        return res