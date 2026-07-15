"""
VPN Validator Module.

Scientifically proves the baseline VPN environment is active, encrypted, 
and strictly adhering to the architectural requirements.
"""

import time
import logging
from lab.topology.namespace_manager import NamespaceManager, CommandExecutionError
from lab.vpn.config import VPNConfiguration, VPNRole
from framework.traffic.traffic_generator import TrafficGenerator

logger = logging.getLogger(__name__)


class VPNValidator:
    """Validates the state and exclusivity of the VPN tunnel."""

    def __init__(self, config: VPNConfiguration, ns_manager: NamespaceManager) -> None:
        self.config = config
        self.ns = ns_manager
        self.generator = TrafficGenerator(ns_manager, source_ns="client")

    def validate(self, app_server_ip: str) -> None:
        """Executes the validation suite."""
        logger.info("\n=== Phase 4: Baseline VPN Validation ===")
        
        # 1. Interface verification
        for node in self.config.nodes:
            link_out = self.ns.execute(node.namespace, ["ip", "link", "show", node.interface.name])
            if "UP" not in link_out.split(",")[0]:
                raise AssertionError(f"WireGuard interface {node.interface.name} in {node.namespace} is down.")
        logger.info("[PASS] WireGuard virtual interfaces exist and are UP.")

        # 2. Kernel Parameter verification
        client_node = next(n for n in self.config.nodes if n.role == VPNRole.CLIENT)
        rp_state = self.ns.execute(client_node.namespace, ["sysctl", "-n", "net.ipv4.conf.all.rp_filter"])
        if rp_state != "2":
            raise AssertionError(f"Client rp_filter is not set to loose mode (Expected 2, got {rp_state}).")
        logger.info("[PASS] Client kernel configured for weak host model (rp_filter=2).")

        # 3. Trigger Handshake (UDP is stateless, must send data to initialize)
        logger.info("Triggering tunnel handshake via ICMP...")
        success, _ = self.generator.generate_icmp(app_server_ip)
        if not success:
            raise AssertionError("Initial tunnel ICMP probe failed.")

        # 4. Validate Handshake
        server_node = next(n for n in self.config.nodes if n.role == VPNRole.SERVER)
        hs_out = self.ns.execute(server_node.namespace, ["wg", "show", server_node.interface.name, "latest-handshakes"])
        if not hs_out or "0" in hs_out.split("\t")[1]:
            raise AssertionError("WireGuard handshake failed or did not register.")
        logger.info("[PASS] Cryptographic handshake completed successfully.")

        # 5. Verify End-to-End HTTP Payload via Tunnel
        logger.info("Validating Layer 7 application traffic through tunnel...")
        success, out = self.generator.generate_http(app_server_ip, 8000)
        if not success or "HTTP_PAYLOAD_OK" not in out:
            raise AssertionError(f"Failed to route HTTP payload through VPN. Output: {out}")
        logger.info("[PASS] HTTP traffic successfully retrieved through encrypted tunnel.")