"""
Runtime Logger Module.

Provides standardized, structured logging for the Experiment Runtime.
Ensures console output is human-readable while generating detailed file logs 
for post-experiment debugging and verification.
"""

import logging
from pathlib import Path
from typing import Optional


def setup_runtime_logger(experiment_name: str, log_dir: Path) -> logging.Logger:
    """
    Configures and retrieves the master logger for a specific experiment run.

    Args:
        experiment_name: Identifier used for naming the log file.
        log_dir: Directory where the log artifact will be stored.

    Returns:
        A configured logging.Logger instance.
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{experiment_name}.log"

    logger = logging.getLogger("ExperimentRuntime")
    # Prevent duplicate handlers if called multiple times in the same session
    if logger.hasHandlers():
        logger.handlers.clear()

    logger.setLevel(logging.DEBUG)

    # Console Handler (INFO level, clean output)
    c_handler = logging.StreamHandler()
    c_handler.setLevel(logging.INFO)
    c_format = logging.Formatter('%(message)s')
    c_handler.setFormatter(c_format)

    # File Handler (DEBUG level, detailed timestamps and module info)
    f_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
    f_handler.setLevel(logging.DEBUG)
    f_format = logging.Formatter('%(asctime)s - [%(levelname)s] - %(name)s - %(message)s')
    f_handler.setFormatter(f_format)

    logger.addHandler(c_handler)
    logger.addHandler(f_handler)

    return logger