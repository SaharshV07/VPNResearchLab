"""
Topology Builder Module.

Orchestrates the Configuration, Namespace, Network, and Routing modules 
to synthesize the complete infrastructure from a declarative YAML file.
"""

import logging
from lab.config import LabConfiguration
from lab.topology.namespace_manager import NamespaceManager, LabConfig as NsConfig
from lab.topology.network_builder import NetworkBuilder
from lab.topology.routing_manager import RoutingManager

logger = logging.getLogger(__name__)


class TopologyBuilder:
    """
    End-to-end orchestrator for the virtual network laboratory.
    """

    def __init__(self, config: LabConfiguration) -> None:
        """
        Initializes the build orchestrator.

        Args:
            config: A validated LabConfiguration instance parsed from YAML.
        """
        self.config = config
        
        # Initialize sub-managers
        ns_names = [ns.name for ns in self.config.namespaces]
        self.namespace_manager = NamespaceManager(NsConfig(namespaces=ns_names))
        self.network_builder = NetworkBuilder(self.namespace_manager)
        self.routing_manager = RoutingManager(self.namespace_manager)

    def build(self) -> None:
        """
        Executes the full provision sequence: Namespaces -> Links -> Addressing -> Routing.
        """
        logger.info("=== Phase 1: Provisioning Namespaces ===")
        for ns in self.config.namespaces:
            self.namespace_manager.create_namespace(ns.name)
            self.namespace_manager.bring_loopback_up(ns.name)
            self.routing_manager.set_forwarding(ns.name, ns.forwarding)

        logger.info("\n=== Phase 2: Establishing Layer 2 Links ===")
        for ns in self.config.namespaces:
            for iface in ns.interfaces:
                if iface.type == "veth" and iface.peer_namespace and iface.peer_name:
                    self.network_builder.create_veth_pair(
                        ns.name, iface.name, iface.peer_namespace, iface.peer_name
                    )

        logger.info("\n=== Phase 3: Layer 3 Addressing & Interface Activation ===")
        for ns in self.config.namespaces:
            for iface in ns.interfaces:
                if iface.ip:
                    self.network_builder.assign_ip(ns.name, iface.name, iface.ip)
                self.network_builder.bring_interface_up(ns.name, iface.name)

        logger.info("\n=== Phase 4: Configuring Routing Tables ===")
        for ns in self.config.namespaces:
            for route in ns.routes:
                self.routing_manager.add_route(
                    ns.name, target=route.target, gateway=route.gateway, dev=route.dev
                )

        logger.info("\n[+] Topology build sequence complete.")

    def teardown(self) -> None:
        """
        Erases the entire configuration footprint from the host kernel.
        """
        logger.info("=== Executing Topology Teardown ===")
        self.namespace_manager.cleanup()