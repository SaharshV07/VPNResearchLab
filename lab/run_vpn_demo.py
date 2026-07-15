#!/usr/bin/env python3
"""
run_vpn_demo.py

Integrates the network configuration and VPN orchestration to deploy and 
validate the baseline encrypted environment.
"""

import sys
import logging
from pathlib import Path

from lab.config import LabConfiguration
from lab.vpn.config import VPNConfiguration
from lab.topology.namespace_manager import NamespaceManager, LabConfig as NsConfig
from lab.vpn.vpn_manager import VPNManager
from lab.vpn.validator import VPNValidator
from lab.start_servers import ServiceOrchestrator

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def format_status(status: bool) -> str:
    """Helper to format boolean checks."""
    return "PASS" if status else "FAIL"


def main() -> None:
    logger.info("Initializing Baseline VPN Environment Deployment...")

    base_dir = Path(__file__).resolve().parent.parent
    vpn_config_path = base_dir / "configs" / "vpn" / "wireguard.yaml"
    # Expected target based on previous infrastructure layout
    app_server_ip = "172.16.1.10"

    try:
        vpn_config = VPNConfiguration.load(vpn_config_path)
        ns_names = [n.namespace for n in vpn_config.nodes] + ["app_server"]
        ns_manager = NamespaceManager(NsConfig(namespaces=ns_names))

        # 1. Deploy VPN
        manager = VPNManager(vpn_config, ns_manager)
        manager.deploy()

        # 2. Start Application Server (Required for Validation)
        orchestrator = ServiceOrchestrator(target_ns="app_server")
        orchestrator.start_all()

        # 3. Validate
        validator = VPNValidator(vpn_config, ns_manager)
        result = validator.validate(app_server_ip)

        # 4. Generate Reporting Block
        print("\n" + "=" * 35)
        print("===== BASELINE VPN VALIDATION =====")
        print("=" * 35)
        print(f"Namespaces ........ {format_status(result.namespaces)}")
        print(f"WireGuard Interface {format_status(result.interfaces)}")
        print(f"Handshake ......... {format_status(result.handshake)}")
        print(f"Routing ........... {format_status(result.routing)}")
        print(f"NAT ............... {format_status(result.nat)}")
        print(f"Connectivity ...... {format_status(result.connectivity)}")
        print("-" * 35)
        print(f"RTT ............... {result.rtt_ms:.2f} ms")
        print(f"Throughput ........ {result.throughput_mbps:.2f} MB/s")
        print("=" * 35 + "\n")

        if not all([result.namespaces, result.interfaces, result.handshake, result.routing, result.nat, result.connectivity]):
            sys.exit(1)

    except Exception as e:
        logger.error(f"Deployment encountered a fatal error: {e}")
        sys.exit(1)
    finally:
        try:
            orchestrator.stop_all()
        except Exception:
            pass

if __name__ == "__main__":
    main()