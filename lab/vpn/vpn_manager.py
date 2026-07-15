"""
VPN Orchestration Manager.

Coordinates end-to-end VPN deployment, including key generation,
interface provisioning, routing overrides, and iptables NAT multiplexing.
"""

import logging
from typing import Dict

from lab.topology.namespace_manager import NamespaceManager
from lab.vpn.config import VPNConfiguration, VPNRole
from lab.vpn.key_manager import WireGuardKeyManager, WireGuardKeyPair
from lab.vpn.wireguard_manager import WireGuardManager

logger = logging.getLogger(__name__)


class VPNManager:
    """Orchestrates the deployment of the baseline encrypted environment."""

    def __init__(
        self,
        config: VPNConfiguration,
        ns_manager: NamespaceManager,
    ) -> None:
        """
        Initializes the VPNManager.

        Args:
            config: The validated VPN configuration schema.
            ns_manager: The underlying namespace command abstraction.
        """
        self.config = config
        self.ns = ns_manager
        self.key_manager = WireGuardKeyManager()
        self.wg_manager = WireGuardManager(ns_manager)

    def deploy(self) -> None:
        """Executes the complete VPN provisioning sequence."""
        logger.info("=== Generating Cryptographic Keys ===")
        keys: Dict[str, WireGuardKeyPair] = {}
        for node in self.config.nodes:
            keys[node.namespace] = self.key_manager.generate_keypair(node.namespace)

        peer_pub_keys = {ns: kp.public_key for ns, kp in keys.items()}

        logger.info("\n=== Provisioning WireGuard Interfaces ===")
        for node in self.config.nodes:
            iface = node.interface.name
            ns = node.namespace

            # 1. Instantiate the physical layer construct
            self.wg_manager.create_interface(ns, iface)

            # 2. Bind the cryptographic properties
            self.wg_manager.generate_and_apply_config(node, keys[ns], peer_pub_keys)

            # 3. Layer 3 Initialization
            self.ns.execute(ns, ["ip", "addr", "add", node.interface.address, "dev", iface])
            self.ns.execute(ns, ["ip", "link", "set", iface, "mtu", str(node.interface.mtu)])
            self.ns.execute(ns, ["ip", "link", "set", iface, "up"])

        logger.info("\n=== Configuring Routing & Security Boundaries ===")
        for node in self.config.nodes:
            ns = node.namespace

            # Apply defined YAML routing
            for route in node.routes:
                cmd = ["ip", "route", "add", route.target]
                if route.gateway:
                    cmd.extend(["via", route.gateway])
                if route.dev:
                    cmd.extend(["dev", route.dev])
                self.ns.execute(ns, cmd)

            # Server-side constraints: Enable forwarding and NAT Multiplexing
            if node.role == VPNRole.SERVER:
                logger.info(f"Enabling IPv4 Forwarding & MASQUERADE on '{ns}'")
                self.ns.execute(ns, ["sysctl", "-w", "net.ipv4.ip_forward=1"])
                # Extract the subnet (e.g. '10.7.0.1/24' -> '10.7.0.0/24')
                ip_prefix = node.interface.address.split('.')[0:3]
                subnet = f"{'.'.join(ip_prefix)}.0/24"
                self.ns.execute(
                    ns,
                    ["iptables", "-t", "nat", "-A", "POSTROUTING", "-s", subnet, "-j", "MASQUERADE"]
                )

            # Client-side constraints: Weak Host Model initialization
            if node.role == VPNRole.CLIENT:
                logger.info(f"Configuring Weak Host Model (rp_filter=2) on '{ns}'")
                self.ns.execute(ns, ["sysctl", "-w", "net.ipv4.conf.all.rp_filter=2"])
                self.ns.execute(ns, ["sysctl", "-w", "net.ipv4.conf.default.rp_filter=2"])