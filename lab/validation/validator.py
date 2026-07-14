"""
Validation Module.

Examines the kernel state of the deployed namespaces to guarantee 
fidelity to the original configuration and verifies end-to-end packet delivery.
"""

import logging
from lab.config import LabConfiguration
from lab.topology.namespace_manager import NamespaceManager, CommandExecutionError

logger = logging.getLogger(__name__)


class LaboratoryValidator:
    """Verifies infrastructure state against the declarative configuration."""

    def __init__(self, config: LabConfiguration, manager: NamespaceManager) -> None:
        self.config = config
        self.manager = manager

    def _get_ip_without_cidr(self, ip_cidr: str) -> str:
        """Extracts the IP from a CIDR string (e.g., '10.0.0.1/24' -> '10.0.0.1')."""
        return ip_cidr.split('/')[0]

    def _get_node_ip(self, ns_name: str) -> str:
        """Locates the first assigned IP address for a given namespace name."""
        for ns in self.config.namespaces:
            if ns.name == ns_name:
                for iface in ns.interfaces:
                    if iface.ip:
                        return self._get_ip_without_cidr(iface.ip)
        raise ValueError(f"No IP address configured for namespace: {ns_name}")

    def validate(self) -> None:
        """
        Executes the comprehensive validation sequence.
        Raises SystemExit(1) if any critical infrastructure component fails.
        """
        logger.info("\n=== Phase 5: Infrastructure Validation ===")
        
        try:
            for ns in self.config.namespaces:
                # 1. Namespaces exist
                if not self.manager.namespace_exists(ns.name):
                    raise AssertionError(f"Namespace '{ns.name}' is missing.")

                # 2. Forwarding state
                fwd_state = self.manager.execute(ns.name, ["sysctl", "-n", "net.ipv4.ip_forward"])
                expected_fwd = "1" if ns.forwarding else "0"
                if fwd_state != expected_fwd:
                    raise AssertionError(f"Namespace '{ns.name}' IPv4 forwarding mismatch.")

                for iface in ns.interfaces:
                    # 3. Interfaces exist & are UP
                    link_out = self.manager.execute(ns.name, ["ip", "link", "show", iface.name])
                    if "UP" not in link_out.split(",")[0]:
                        raise AssertionError(f"Interface '{iface.name}' in '{ns.name}' is not UP.")

                    # 4. Correct IPs
                    if iface.ip:
                        addr_out = self.manager.execute(ns.name, ["ip", "addr", "show", iface.name])
                        if iface.ip not in addr_out:
                            raise AssertionError(f"IP '{iface.ip}' not assigned to '{iface.name}' in '{ns.name}'.")

                # 5. Correct Routes
                route_out = self.manager.execute(ns.name, ["ip", "route", "show"])
                for route in ns.routes:
                    if route.target == "0.0.0.0/0":
                        if f"default via {route.gateway}" not in route_out:
                            raise AssertionError(f"Missing default gateway in '{ns.name}'.")
                    else:
                        if route.target not in route_out:
                            raise AssertionError(f"Missing route to '{route.target}' in '{ns.name}'.")

            logger.info("[PASS] Kernel State Validation: Namespaces, Interfaces, IPs, Routes, and Forwarding verified.")

            # 6. End-to-End Ping
            app_ip = self._get_node_ip("app_server")
            logger.info(f"Testing ICMP routing: Client -> App Server ({app_ip})")
            self.manager.execute("client", ["ping", "-c", "1", "-W", "1", app_ip])
            logger.info("[PASS] Forward Ping Successful.")

            # 7. Reverse Ping
            client_ip = self._get_node_ip("client")
            logger.info(f"Testing ICMP routing: App Server -> Client ({client_ip})")
            self.manager.execute("app_server", ["ping", "-c", "1", "-W", "1", client_ip])
            logger.info("[PASS] Reverse Ping Successful.")

            logger.info("\n[SUCCESS] Laboratory infrastructure is completely operational.")

        except (CommandExecutionError, AssertionError, ValueError) as e:
            logger.error(f"\n[FAIL] Validation Failed: {e}")
            raise SystemExit(1)