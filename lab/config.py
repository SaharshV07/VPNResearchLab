"""
Configuration module for VPNResearchLab.

Parses, validates, and models the laboratory topology defined in YAML.
Ensures consistency of IPs, subnets, interfaces, and routes before execution.
"""

import yaml
import ipaddress
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


# --- Exceptions ---

class ConfigurationError(Exception):
    """Base exception for all configuration validation errors."""
    pass


class DuplicateNamespaceError(ConfigurationError):
    """Raised when a namespace name is defined more than once."""
    pass


class DuplicateInterfaceError(ConfigurationError):
    """Raised when an interface name is defined more than once across the topology."""
    pass


class InvalidCIDRError(ConfigurationError):
    """Raised when an invalid CIDR notation is provided for a subnet."""
    pass


class InvalidIPError(ConfigurationError):
    """Raised when an interface or gateway IP is invalid."""
    pass


class MissingGatewayError(ConfigurationError):
    """Raised when a route target requires a gateway but none is provided."""
    pass


class TopologyConsistencyError(ConfigurationError):
    """Raised when references (e.g., peer namespaces, capture points) are missing."""
    pass


# --- Dataclasses ---

@dataclass(frozen=True, slots=True)
class RouteConfiguration:
    target: str
    gateway: Optional[str] = None
    dev: Optional[str] = None


@dataclass(frozen=True, slots=True)
class InterfaceConfiguration:
    name: str
    type: str
    ip: Optional[str] = None
    peer_namespace: Optional[str] = None
    peer_name: Optional[str] = None


@dataclass(frozen=True, slots=True)
class CapturePointConfiguration:
    namespace: str
    interface: str
    bpf_filter: str = ""


@dataclass(frozen=True, slots=True)
class NamespaceConfiguration:
    name: str
    forwarding: bool
    interfaces: List[InterfaceConfiguration] = field(default_factory=list)
    routes: List[RouteConfiguration] = field(default_factory=list)
    vpn_config: Optional[Dict[str, str]] = None


@dataclass(frozen=True, slots=True)
class LabConfiguration:
    lab_name: str
    description: str
    subnets: List[str]
    namespaces: List[NamespaceConfiguration]
    capture_points: List[CapturePointConfiguration]

    @classmethod
    def load(cls, path: Path) -> "LabConfiguration":
        """Loads and parses the YAML configuration into dataclasses."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Malformed YAML in {path}: {e}")
        except FileNotFoundError:
            raise ConfigurationError(f"Configuration file not found: {path}")

        namespaces = []
        for ns_data in data.get("namespaces", []):
            interfaces = [
                InterfaceConfiguration(**iface_data) 
                for iface_data in ns_data.get("interfaces", [])
            ]
            routes = [
                RouteConfiguration(**route_data) 
                for route_data in ns_data.get("routes", [])
            ]
            namespaces.append(
                NamespaceConfiguration(
                    name=ns_data["name"],
                    forwarding=ns_data.get("forwarding", False),
                    interfaces=interfaces,
                    routes=routes,
                    vpn_config=ns_data.get("vpn_config")
                )
            )

        capture_points = [
            CapturePointConfiguration(**cp_data) 
            for cp_data in data.get("capture_points", [])
        ]

        config = cls(
            lab_name=data.get("lab_name", "unnamed_lab"),
            description=data.get("description", ""),
            subnets=data.get("subnets", []),
            namespaces=namespaces,
            capture_points=capture_points,
        )
        config.validate()
        return config

    def validate(self) -> None:
        """
        Validates the entirety of the laboratory configuration for correctness and consistency.
        Raises specific exceptions upon encountering invalid data.
        """
        # Validate Subnets
        for subnet in self.subnets:
            try:
                ipaddress.IPv4Network(subnet, strict=False)
            except ValueError:
                raise InvalidCIDRError(f"Invalid subnet CIDR: {subnet}")

        seen_namespaces = set()
        seen_interfaces = set()

        for ns in self.namespaces:
            # Validate Namespace Uniqueness
            if ns.name in seen_namespaces:
                raise DuplicateNamespaceError(f"Duplicate namespace detected: {ns.name}")
            seen_namespaces.add(ns.name)

            for iface in ns.interfaces:
                # Validate Interface Uniqueness
                if iface.name in seen_interfaces:
                    raise DuplicateInterfaceError(f"Duplicate interface detected globally: {iface.name}")
                seen_interfaces.add(iface.name)

                # Validate Interface IP
                if iface.ip:
                    try:
                        ipaddress.IPv4Interface(iface.ip)
                    except ValueError:
                        raise InvalidIPError(f"Invalid interface IP on {iface.name}: {iface.ip}")

            for route in ns.routes:
                # Validate Route Target
                if route.target != "0.0.0.0/0":
                    try:
                        ipaddress.IPv4Network(route.target, strict=False)
                    except ValueError:
                        raise InvalidCIDRError(f"Invalid route target in {ns.name}: {route.target}")

                # Validate Gateway Presence
                if not route.gateway and not route.dev:
                    raise MissingGatewayError(f"Route for {route.target} in {ns.name} requires a gateway or dev.")

                # Validate Gateway IP
                if route.gateway:
                    try:
                        ipaddress.IPv4Address(route.gateway)
                    except ValueError:
                        raise InvalidIPError(f"Invalid gateway IP in {ns.name}: {route.gateway}")

        # Validate Cross-References (Peers and Capture Points)
        for ns in self.namespaces:
            for iface in ns.interfaces:
                if iface.peer_namespace and iface.peer_namespace not in seen_namespaces:
                    raise TopologyConsistencyError(
                        f"Interface {iface.name} references non-existent peer namespace: {iface.peer_namespace}"
                    )

        for cp in self.capture_points:
            if cp.namespace not in seen_namespaces:
                raise TopologyConsistencyError(f"Capture point references non-existent namespace: {cp.namespace}")