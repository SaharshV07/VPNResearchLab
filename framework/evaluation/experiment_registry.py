"""
Experiment Registry Module.

Responsible for registering unique experiment executions, capturing software 
environments, and generating cryptographic hashes of configuration files to 
guarantee reproducibility.
"""

import hashlib
import platform
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass(frozen=True, slots=True)
class ExperimentRecord:
    """Immutable record containing the unique identity of an experiment run."""
    experiment_id: str
    version: str
    timestamp: float
    config_hash: str
    os_info: str
    python_version: str


class ExperimentRegistry:
    """Registers and fingerprints experiments before execution."""

    @staticmethod
    def _hash_files(file_paths: List[Path]) -> str:
        """
        Generates a SHA-256 hash of the provided configuration files.
        
        Args:
            file_paths: List of paths to configuration files (e.g., YAMLs).
            
        Returns:
            A hex digest string representing the combined state of the configs.
        """
        sha256 = hashlib.sha256()
        for path in sorted(file_paths):
            if path.exists():
                sha256.update(path.name.encode('utf-8'))
                sha256.update(path.read_bytes())
            else:
                sha256.update(b"MISSING_FILE")
        return sha256.hexdigest()

    @classmethod
    def register(cls, experiment_id: str, version: str, config_paths: List[Path]) -> ExperimentRecord:
        """
        Creates a reproducible footprint for the current experiment execution.
        
        Args:
            experiment_id: Unique identifier for the experiment (e.g., 'exp_01_vip').
            version: Experiment iteration or framework version.
            config_paths: Configuration files driving the topology and VPN.
            
        Returns:
            An ExperimentRecord dataclass.
        """
        config_hash = cls._hash_files(config_paths)
        
        return ExperimentRecord(
            experiment_id=experiment_id,
            version=version,
            timestamp=time.time(),
            config_hash=config_hash,
            os_info=f"{platform.system()} {platform.release()} ({platform.machine()})",
            python_version=platform.python_version()
        )