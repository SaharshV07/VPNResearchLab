#!/usr/bin/env python3
"""
run_verification.py

Entry point to execute the baseline verification suite and generate reports.
Assumes the laboratory and VPN environment have already been spun up.
"""

import os
import sys
import logging
from pathlib import Path

from lab.config import LabConfiguration
from lab.vpn.config import VPNConfiguration
from lab.topology.namespace_manager import NamespaceManager, LabConfig as NsConfig
from lab.validation.verification_runner import VerificationSuite
from lab.validation.report_generator import ReportGenerator

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    if not is_admin():
        logger.error("FATAL: Root privileges required for kernel state queries.")
        sys.exit(1)

    base_dir = Path(__file__).resolve().parent.parent
    lab_config_path = base_dir / "configs" / "topology.yaml"
    vpn_config_path = base_dir / "configs" / "vpn" / "wireguard.yaml"
    reports_dir = base_dir / "reports"

    try:
        # Load configurations
        lab_config = LabConfiguration.load(lab_config_path)
        vpn_config = VPNConfiguration.load(vpn_config_path)
        
        # Initialize Namespace Manager
        ns_names = [ns.name for ns in lab_config.namespaces]
        ns_manager = NamespaceManager(NsConfig(namespaces=ns_names))
        
        # Run Verification
        runner = VerificationSuite(lab_config, vpn_config, ns_manager)
        results = runner.run_all()
        
        # Generate Reports
        logger.info("=== Generating Artifacts ===")
        generator = ReportGenerator(results, reports_dir)
        json_file = generator.generate_json()
        md_file = generator.generate_markdown()
        
        logger.info(f"[+] JSON Report saved to: {json_file}")
        logger.info(f"[+] Markdown Report saved to: {md_file}")
        
        # Final Status
        if all(all(checks.values()) for checks in results["checks"].values()):
            logger.info("\n[SUCCESS] Baseline Environment is perfectly aligned with paper assumptions.")
        else:
            logger.error("\n[FAIL] Baseline Environment verification failed. Check the Markdown report.")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Verification execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()