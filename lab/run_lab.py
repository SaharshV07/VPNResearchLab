#!/usr/bin/env python3
"""
run_lab.py

Main entry point to parse configuration, build the laboratory, and validate connectivity.
"""

import os
import sys
import logging
from pathlib import Path

from lab.config import LabConfiguration, ConfigurationError
from lab.topology.topology_builder import TopologyBuilder
from lab.validation.validator import LaboratoryValidator

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

def main() -> None:
    if os.geteuid() != 0:
        logger.error("FATAL: Provisioning requires root privileges (run with sudo).")
        sys.exit(1)

    config_path = Path(__file__).resolve().parent.parent / "configs" / "topology.yaml"
    
    try:
        # Load and validate YAML config
        logger.info(f"Loading configuration from {config_path}...")
        config = LabConfiguration.load(config_path)
        
        builder = TopologyBuilder(config)
        
        # Ensure a clean slate
        builder.teardown()
        
        # Provision network
        builder.build()
        
        # Verify network
        validator = LaboratoryValidator(config, builder.namespace_manager)
        validator.validate()
        
    except ConfigurationError as e:
        logger.error(f"Configuration Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Execution Error: {e}")
        # builder.teardown() could be called here to rollback on failure
        sys.exit(1)

if __name__ == "__main__":
    main()