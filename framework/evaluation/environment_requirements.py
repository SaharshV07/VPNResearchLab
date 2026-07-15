"""
Environment Requirements Module.

Defines the precise topology, background services, interfaces, and 
configuration versions necessary for an experiment to execute safely.
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class EnvironmentRequirements:
    """
    Strict schema representing the required state of the network environment.
    
    Attributes:
        namespaces: List of network namespaces that must exist.
        vpn_required: Boolean indicating if an active VPN tunnel is strictly required.
        required_services: List of background listeners (e.g., 'http:8000') that must be active.
        required_interfaces: List of interface names (e.g., 'wg0') that must be UP.
        config_versions: Dictionary mapping configuration categories to expected version strings.
    """
    namespaces: List[str] = field(default_factory=list)
    vpn_required: bool = True
    required_services: List[str] = field(default_factory=list)
    required_interfaces: List[str] = field(default_factory=list)
    config_versions: Dict[str, str] = field(default_factory=dict)

    def validate_config_versions(self, actual_versions: Dict[str, str]) -> None:
        """
        Verifies that the currently loaded configuration versions match the requirements.
        
        Args:
            actual_versions: A dictionary of currently active versions.
            
        Raises:
            ValueError: If a required configuration version does not match.
        """
        for config_key, expected_version in self.config_versions.items():
            actual_version = actual_versions.get(config_key)
            if actual_version != expected_version:
                raise ValueError(
                    f"Configuration version mismatch for '{config_key}'. "
                    f"Expected '{expected_version}', got '{actual_version}'."
                )