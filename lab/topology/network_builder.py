"""
Network Builder Module.

Abstracts the creation of virtual ethernet pairs, interface state management,
and IP address assignment within Linux network namespaces.
"""

import subprocess
import logging
from typing import Set, Tuple
from lab.topology.namespace_manager import NamespaceManager, CommandExecutionError

logger = logging.getLogger(__name__)


class NetworkBuilder:
    """
    Manages Layer 2 links (veth pairs) and Layer 3 addressing (IPs).
    Ensures idempotency by tracking initialized interfaces.
    """

    def __init__(self, manager: NamespaceManager) -> None:
        """
        Initializes the NetworkBuilder.

        Args:
            manager: An active instance of NamespaceManager for command execution.
        """
        self.manager = manager
        self._created_veths: Set[Tuple[str, str]] = set()

    def create_veth_pair(self, ns1: str, if1: str, ns2: str, if2: str) -> None:
        """
        Creates a virtual ethernet pair and moves the endpoints to their respective namespaces.
        Tracks created pairs to avoid duplicate creation errors.

        Args:
            ns1: First namespace.
            if1: Interface name in the first namespace.
            ns2: Second namespace.
            if2: Interface name in the second namespace.
        
        Raises:
            CommandExecutionError: If veth creation fails on the host.
        """
        # Lexicographical sort to create a unique identifier for the connection
        pair_id = tuple(sorted([f"{ns1}:{if1}", f"{ns2}:{if2}"]))
        if pair_id in self._created_veths:
            return

        try:
            logger.info(f"Operation='create_veth' Pair='{ns1}:{if1} <-> {ns2}:{if2}' Status='STARTED'")
            # Create the pair on the root host network stack
            subprocess.run(
                ["ip", "link", "add", if1, "type", "veth", "peer", "name", if2],
                check=True, capture_output=True, text=True
            )
            # Migrate the endpoints into the isolated namespaces
            subprocess.run(["ip", "link", "set", if1, "netns", ns1], check=True, capture_output=True)
            subprocess.run(["ip", "link", "set", if2, "netns", ns2], check=True, capture_output=True)
            
            self._created_veths.add(pair_id)
            logger.debug(f"Operation='create_veth' Pair='{ns1}:{if1} <-> {ns2}:{if2}' Status='SUCCESS'")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Operation='create_veth' Status='FAILURE' Details='{e.stderr.strip()}'")
            raise CommandExecutionError(f"Failed to create veth pair: {e.stderr.strip()}")

    def assign_ip(self, ns: str, iface: str, ip_cidr: str) -> None:
        """
        Assigns an IPv4 address and subnet mask to a specific interface.

        Args:
            ns: The target namespace.
            iface: The target interface.
            ip_cidr: The IPv4 address in CIDR notation (e.g., 192.168.1.10/24).
        """
        self.manager.execute(ns, ["ip", "addr", "add", ip_cidr, "dev", iface])
        logger.info(f"Operation='assign_ip' Namespace='{ns}' Interface='{iface}' IP='{ip_cidr}' Status='SUCCESS'")

    def bring_interface_up(self, ns: str, iface: str) -> None:
        """
        Changes the administrative state of a network interface to UP.

        Args:
            ns: The target namespace.
            iface: The target interface.
        """
        self.manager.execute(ns, ["ip", "link", "set", iface, "up"])
        logger.info(f"Operation='bring_up' Namespace='{ns}' Interface='{iface}' Status='SUCCESS'")