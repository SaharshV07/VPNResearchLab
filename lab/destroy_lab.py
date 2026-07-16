#!/usr/bin/env python3
"""
destroy_lab.py

Entry point to parse configuration and strictly teardown the laboratory.
"""

import os
import sys
import logging
from pathlib import Path

from lab.config import LabConfiguration
from lab.topology.topology_builder import TopologyBuilder

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

import sys
import logging
from framework.utils.platform import is_admin

logger = logging.getLogger(__name__)

def main() -> None:
    if not is_admin():
        logger.error("FATAL: Root/Administrative privileges required for kernel network manipulation.")
        sys.exit(1)
    
    # ... rest of execution logic

def main() -> None:
    if is_admin() != 0:
        logger.error("FATAL: Teardown requires root privileges (run with sudo).")
        sys.exit(1)

    config_path = Path(__file__).resolve().parent.parent / "configs" / "topology.yaml"
    
    try:
        config = LabConfiguration.load(config_path)
        builder = TopologyBuilder(config)
        builder.teardown()
    except Exception as e:
        logger.error(f"Teardown Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()