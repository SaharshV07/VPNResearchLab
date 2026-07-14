"""
Routing Manager Module.

Abstracts the configuration of static routes and kernel IP forwarding.
"""

import logging
from typing import Optional
from lab.topology.namespace_manager import NamespaceManager

logger = logging.getLogger(__name__)


class RoutingManager:
    """
    Manages Layer 3 routing tables and IP forwarding configurations.
    """

    def __init__(self, manager: NamespaceManager) -> None:
        """
        Initializes the RoutingManager.

        Args:
            manager: An active instance of NamespaceManager for command execution.
        """
        self.manager = manager

    def set_forwarding(self, ns: str, enabled: bool) -> None:
        """
        Toggles IPv4 forwarding within a namespace.

        Args:
            ns: The target namespace.
            enabled: True to enable forwarding, False to disable.
        """
        if enabled:
            self.manager.enable_ipv4_forwarding(ns)
        else:
            self.manager.disable_ipv4_forwarding(ns)

    def add_route(self, ns: str, target: str, gateway: Optional[str] = None, dev: Optional[str] = None) -> None:
        """
        Adds a static route to the routing table of a namespace.
        If the target is '0.0.0.0/0', configures the default gateway.

        Args:
            ns: The target namespace.
            target: The destination CIDR block.
            gateway: The next-hop IP address (optional).
            dev: The egress interface name (optional).
        """
        cmd = ["ip", "route", "add", target]
        if gateway:
            cmd.extend(["via", gateway])
        if dev:
            cmd.extend(["dev", dev])

        self.manager.execute(ns, cmd)
        route_desc = f"{target} via {gateway or dev}"
        logger.info(f"Operation='add_route' Namespace='{ns}' Route='{route_desc}' Status='SUCCESS'")