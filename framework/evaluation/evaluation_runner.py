"""
Evaluation Runner Module.

Performs stringent pre-execution sanity checks to guarantee the laboratory 
topology, VPN state, and background services are healthy before research begins.
"""

import logging
from pathlib import Path
from typing import List

from lab.config import LabConfiguration
from lab.vpn.config import VPNConfiguration
from lab.topology.namespace_manager import NamespaceManager
from lab.vpn.validator import VPNValidator

logger = logging.getLogger(__name__)


class EvaluationValidator:
    """Pre-flight validation harness for networking experiments."""

    def __init__(
        self,
        lab_config: LabConfiguration,
        vpn_config: VPNConfiguration,
        ns_manager: NamespaceManager
    ):
        self.lab_config = lab_config
        self.vpn_config = vpn_config
        self.ns = ns_manager

    def validate_configs_exist(self, config_paths: List[Path]) -> None:
        """Verifies that all required configuration files exist on disk."""
        for path in config_paths:
            if not path.exists():
                raise FileNotFoundError(f"Required configuration file missing: {path}")
        logger.info("[PASS] Configuration files verified.")

    def validate_namespaces(self) -> None:
        """Verifies all expected namespaces are present in the kernel."""
        for ns in self.lab_config.namespaces:
            if not self.ns.namespace_exists(ns.name):
                raise RuntimeError(f"Expected namespace '{ns.name}' is missing.")
        logger.info("[PASS] Expected namespaces verified.")

    def validate_services(self) -> None:
        """
        Verifies that background application services are listening 
        in the app_server namespace using the 'ss' socket statistics utility.
        """
        try:
            # Check for TCP 8000, 9000 and UDP 9001, 9053
            out = self.ns.execute("app_server", ["ss", "-tuln"])
            required_ports = [":8000", ":9000", ":9001", ":9053"]
            for port in required_ports:
                if port not in out:
                    raise RuntimeError(f"Required service on port {port} is not listening in app_server.")
            logger.info("[PASS] Background services verified.")
        except Exception as e:
            raise RuntimeError(f"Failed to validate services: {e}")

    def validate_vpn_baseline(self) -> None:
        """
        Leverages the VPNValidator to strictly assert VPN encryption,
        routing, and NAT states before the experiment starts.
        """
        try:
            # Locate App Server IP
            app_ip = ""
            for ns in self.lab_config.namespaces:
                if ns.name == "app_server":
                    app_ip = ns.interfaces[0].ip.split('/')[0]
                    
            if not app_ip:
                raise ValueError("Could not resolve app_server IP.")

            validator = VPNValidator(self.vpn_config, self.ns)
            res = validator.validate(app_ip)
            
            if not all([res.namespaces, res.interfaces, res.handshake, res.routing, res.nat, res.connectivity]):
                raise RuntimeError("Baseline VPN environment failed one or more integrity checks.")
                
            logger.info("[PASS] VPN Baseline integrity verified.")
        except Exception as e:
            raise RuntimeError(f"VPN validation error: {e}")

    def run_pre_flight_checks(self, config_paths: List[Path]) -> None:
        """
        Executes the entire validation chain. Terminates gracefully on failure.
        """
        logger.info("=== Executing Evaluation Pre-Flight Checks ===")
        try:
            self.validate_configs_exist(config_paths)
            self.validate_namespaces()
            self.validate_services()
            self.validate_vpn_baseline()
            logger.info("=== Pre-Flight Checks Successful ===")
        except Exception as e:
            logger.error(f"[FATAL] Evaluation Harness Pre-Flight Failed: {e}")
            raise SystemExit(1)