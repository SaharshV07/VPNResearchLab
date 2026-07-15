"""
VPN Orchestration Manager.

Coordinates the end-to-end deployment of the VPN topology. 
Handles key generation, interface provisioning, routing overrides, and NAT.
"""

import logging
from typing import Dict

from lab.topology.namespace_manager import NamespaceManager
from lab.topology.routing_manager import RoutingManager
from lab.topology.network_builder import NetworkBuilder
from lab.vpn.config import VPNConfiguration, VPNRole
from lab.vpn.key_manager import WireGuardKeyManager, WireGuardKeyPair
from lab.vpn.wireguard_manager import WireGuardManager

logger = logging.getLogger(__name__)


class VPNManager:
    """Orchestrates the deployment of the baseline VPN environment."""

    def __init__(
        self, 
        config: VPNConfiguration, 
        ns_manager: NamespaceManager,
        route_manager: RoutingManager,
        net_builder: NetworkBuilder
    ) -> None:
        self.config = config
        self.ns = ns_manager
        self.route = route_manager
        self.net = net_builder
        self.key_manager = WireGuardKeyManager()
        self.wg_manager = WireGuardManager(ns_manager)

    def deploy(self) -> None:
        """Executes the complete VPN deployment sequence."""
        logger.info("\n=== Phase 1: Cryptographic Key Generation ===")
        keys: Dict[str, WireGuardKeyPair] = {}
        for node in self.config.nodes:
            keys[node.namespace] = self.key_manager.generate_keypair(node.namespace)

        peer_pub_keys = {ns: kp.public_key for ns, kp in keys.items()}

        logger.info("\n=== Phase 2: Interface Provisioning & Configuration ===")
        for node in self.config.nodes:
            # 1. Create interface
            self.wg_manager.create_interface(node.namespace, node.interface.name)
            
            # 2. Apply WireGuard Configuration
            self.wg_manager.generate_and_apply_config(node, keys[node.namespace], peer_pub_keys)
            
            # 3. Assign IP and bring UP
            self.net.assign_ip(node.namespace, node.interface.name, node.interface.address)
            self.ns.execute(node.namespace, ["ip", "link", "set", node.interface.name, "mtu", str(node.interface.mtu)])
            self.net.bring_interface_up(node.namespace, node.interface.name)

        logger.info("\n=== Phase 3: Network Routing & Kernel Parameters ===")
        for node in self.config.nodes:
            # Endpoint protection: Prevent the tunnel from collapsing its own physical route
            if node.role == VPNRole.CLIENT:
                for peer in node.peers:
                    if peer.endpoint:
                        endpoint_ip = peer.endpoint.split(":")[0]
                        # Route endpoint traffic via the physical gateway (assuming standard lab topology)
                        self.route.add_route(node.namespace, f"{endpoint_ip}/32", gateway="192.168.1.1")

            # Apply YAML routes
            for route in node.routes:
                self.route.add_route(node.namespace, route.target, gateway=route.gateway, dev=route.dev)

            # Establish NAT (Masquerade) on the VPN Server
            if node.role == VPNRole.SERVER:
                logger.info(f"Operation='enable_nat' Namespace='{node.namespace}'")
                # Forward VPN subnet traffic out of the physical interface
                # iptables -t nat -A POSTROUTING -s <vpn_subnet> -j MASQUERADE
                vpn_subnet = "10.7.0.0/24"
                self.ns.execute(
                    node.namespace, 
                    ["iptables", "-t", "nat", "-A", "POSTROUTING", "-s", vpn_subnet, "-j", "MASQUERADE"]
                )
                self.route.set_forwarding(node.namespace, True)

            # Apply Weak Host Model (rp_filter=2) on the Client
            if node.role == VPNRole.CLIENT:
                logger.info(f"Operation='set_rp_filter' Namespace='{node.namespace}' Mode='Loose (2)'")
                self.ns.execute(node.namespace, ["sysctl", "-w", "net.ipv4.conf.all.rp_filter=2"])
                self.ns.execute(node.namespace, ["sysctl", "-w", "net.ipv4.conf.default.rp_filter=2"])