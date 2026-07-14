#!/usr/bin/env python3
"""
Traffic Foundation Demo.

Proves complete end-to-end routing capabilities of the lab.
Spawns servers in the App Server namespace and triggers clients in the Client namespace.
"""

import os
import sys
import time
import logging
from pathlib import Path

from lab.config import LabConfiguration
from lab.topology.namespace_manager import NamespaceManager, LabConfig as NsConfig
from framework.traffic.traffic_generator import TrafficGenerator
from framework.traffic.traffic_validator import TrafficValidator
from lab.start_servers import ServiceOrchestrator

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    if os.geteuid() != 0:
        logger.error("FATAL: Generating namespace traffic requires root privileges (run with sudo).")
        sys.exit(1)

    config_path = Path(__file__).resolve().parent.parent / "configs" / "topology.yaml"
    config = LabConfiguration.load(config_path)
    
    # Extract target App Server IP directly from the configuration system
    target_ip = None
    for ns in config.namespaces:
        if ns.name == "app_server":
            target_ip = ns.interfaces[0].ip.split('/')[0]
            break
            
    if not target_ip:
        logger.error("Could not locate app_server IP in configuration.")
        sys.exit(1)

    # Initialize tools
    ns_manager = NamespaceManager(NsConfig(namespaces=["client"]))
    generator = TrafficGenerator(ns_manager, source_ns="client")
    orchestrator = ServiceOrchestrator(target_ns="app_server")

    try:
        orchestrator.start_all()
        # Allow servers 1 second to bind to sockets
        time.sleep(1)

        logger.info(f"\n=== Executing Traffic Generation (Target: {target_ip}) ===")
        results = []

        # 1. ICMP
        success, out = generator.generate_icmp(target_ip)
        results.append(TrafficValidator.validate_icmp(success, out))

        # 2. TCP
        success, out = generator.generate_tcp(target_ip, 9000)
        results.append(TrafficValidator.validate_tcp(success, out))

        # 3. UDP
        success, out = generator.generate_udp(target_ip, 9001)
        results.append(TrafficValidator.validate_udp(success, out))

        # 4. HTTP
        success, out = generator.generate_http(target_ip, 8000)
        results.append(TrafficValidator.validate_http(success, out))

        # 5. DNS
        success, out = generator.generate_dns(target_ip, 9053)
        results.append(TrafficValidator.validate_dns(success, out))

        # Print Statistics Summary
        logger.info("\n=== Traffic Validation Summary ===")
        for res in results:
            status = "PASS" if (res.success and res.payload_match) else "FAIL"
            latency_str = f"{res.latency_ms:.2f} ms" if res.success else "N/A"
            logger.info(f"{res.protocol:<6} | {status:<4} | RTT: {latency_str:<8} | Match: {str(res.payload_match):<5}")
            if not res.success or not res.payload_match:
                logger.error(f"       -> Error: {res.error_msg}")

    finally:
        orchestrator.stop_all()


if __name__ == "__main__":
    main()