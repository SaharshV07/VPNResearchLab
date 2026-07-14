"""
VPN Configuration Module.

Parses, models, and strictly validates protocol-agnostic VPN topologies 
from YAML definitions. Does not execute or configure network state.
"""

import yaml
import ipaddress
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional, Any
from enum import Enum


# --- Exceptions ---

class VPNConfigurationError(Exception):
    """Base exception for VPN configuration validation errors."""
    pass


class VPNInvalidCIDRError(VPNConfigurationError):
    """Raised when an invalid IPv4 CIDR is provided for a tunnel interface or allowed IPs."""
    pass


class VPNInvalidEndpointError(VPNConfigurationError):
    """Raised when an endpoint is improperly formatted (e.g., missing port)."""
    pass


class VPNPeerResolutionError(VPNConfigurationError):
    """Raised when a peer references a target_namespace that is not defined in the configuration."""
    pass


class VPNUnsupportedProtocolError(VPNConfigurationError):
    """Raised when the specified VPN protocol is not supported by the framework."""
    pass


# --- Enums ---

class VPNProtocol(Enum):
    """Supported VPN implementations."""
    WIREGUARD = "wireguard"
    OPENVPN = "openvpn"


class VPNRole(Enum):
    """Node roles within the VPN topology."""
    CLIENT = "client"
    SERVER = "server"


# --- Dataclasses ---

@dataclass(frozen=True, slots=True)
class VPNInterfaceConfiguration:
    name: str
    address: str
    listen_port: Optional[int] = None
    mtu: int = 1500


@dataclass(frozen=True, slots=True)
class VPNPeerConfiguration:
    target_namespace: str
    allowed_ips: List[str]
    endpoint: Optional[str] = None
    persistent_keepalive: Optional[int] = None


@dataclass(frozen=True, slots=True)
class VPNRouteConfiguration:
    target: str
    dev: str
    gateway: Optional[str] = None


@dataclass(frozen=True, slots=True)
class VPNNodeConfiguration:
    namespace: str
    role: VPNRole
    interface: VPNInterfaceConfiguration
    peers: List[VPNPeerConfiguration] = field(default_factory=list)
    routes: List[VPNRouteConfiguration] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class VPNConfiguration:
    name: str
    protocol: VPNProtocol
    nodes: List[VPNNodeConfiguration]

    @classmethod
    def load(cls, path: Path) -> "VPNConfiguration":
        """
        Loads and parses a VPN YAML configuration into strict dataclass models.

        Args:
            path: The file path to the YAML configuration.

        Returns:
            A populated and validated VPNConfiguration instance.

        Raises:
            VPNConfigurationError: If the file is missing or contains malformed YAML.
        """
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise VPNConfigurationError(f"Malformed YAML in {path}: {e}")
        except FileNotFoundError:
            raise VPNConfigurationError(f"VPN configuration file not found: {path}")

        try:
            protocol = VPNProtocol(data.get("protocol", "").lower())
        except ValueError:
            raise VPNUnsupportedProtocolError(f"Unsupported protocol: {data.get('protocol')}")

        nodes = []
        for node_data in data.get("nodes", []):
            iface_data = node_data.get("interface", {})
            interface = VPNInterfaceConfiguration(
                name=iface_data["name"],
                address=iface_data["address"],
                listen_port=iface_data.get("listen_port"),
                mtu=iface_data.get("mtu", 1500)
            )

            peers = [
                VPNPeerConfiguration(**peer_data) 
                for peer_data in node_data.get("peers", [])
            ]
            
            routes = [
                VPNRouteConfiguration(**route_data)
                for route_data in node_data.get("routes", [])
            ]

            nodes.append(
                VPNNodeConfiguration(
                    namespace=node_data["namespace"],
                    role=VPNRole(node_data["role"].lower()),
                    interface=interface,
                    peers=peers,
                    routes=routes
                )
            )

        config = cls(
            name=data.get("name", "unnamed_vpn"),
            protocol=protocol,
            nodes=nodes
        )
        config.validate()
        return config

    def validate(self) -> None:
        """
        Validates internal consistency, CIDR boundaries, and peer references.
        """
        registered_namespaces = {node.namespace for node in self.nodes}

        for node in self.nodes:
            # Validate interface IP
            try:
                ipaddress.IPv4Interface(node.interface.address)
            except ValueError:
                raise VPNInvalidCIDRError(f"Invalid interface CIDR '{node.interface.address}' on node '{node.namespace}'")

            # Validate Listen Port boundaries
            if node.interface.listen_port is not None:
                if not (0 < node.interface.listen_port <= 65535):
                    raise VPNConfigurationError(f"Listen port {node.interface.listen_port} out of range on node '{node.namespace}'")

            for peer in node.peers:
                # Validate Peer Namespace Reference
                if peer.target_namespace not in registered_namespaces:
                    raise VPNPeerResolutionError(
                        f"Node '{node.namespace}' references unknown peer namespace: '{peer.target_namespace}'"
                    )

                # Validate Allowed IPs
                for ip in peer.allowed_ips:
                    try:
                        ipaddress.IPv4Network(ip, strict=False)
                    except ValueError:
                        raise VPNInvalidCIDRError(f"Invalid allowed_ips CIDR '{ip}' for peer '{peer.target_namespace}'")

                # Validate Endpoint formatting (IP:Port)
                if peer.endpoint:
                    parts = peer.endpoint.split(":")
                    if len(parts) != 2:
                        raise VPNInvalidEndpointError(f"Endpoint '{peer.endpoint}' must be in IP:PORT format.")
                    try:
                        ipaddress.IPv4Address(parts[0])
                        port = int(parts[1])
                        if not (0 < port <= 65535):
                            raise ValueError
                    except ValueError:
                        raise VPNInvalidEndpointError(f"Invalid endpoint IP or Port in '{peer.endpoint}'")

            for route in node.routes:
                # Validate Route Targets
                if route.target != "0.0.0.0/0":
                    try:
                        ipaddress.IPv4Network(route.target, strict=False)
                    except ValueError:
                        raise VPNInvalidCIDRError(f"Invalid route target CIDR '{route.target}' on node '{node.namespace}'")