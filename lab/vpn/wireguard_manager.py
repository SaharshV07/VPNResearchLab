"""
WireGuard Manager Module.

Provides low-level orchestration of WireGuard interfaces and configurations.
Translates Python dataclasses into native wg0.conf formats and applies them 
within isolated network namespaces.
"""

import os
import logging
from typing import Dict
from pathlib import Path

from lab.topology.namespace_manager import NamespaceManager
from lab.vpn.config import VPNNodeConfiguration
from lab.vpn.key_manager import WireGuardKeyPair

logger = logging.getLogger(__name__)


class WireGuardManager:
    """Handles the creation, configuration, and destruction of WireGuard interfaces."""

    def __init__(self, ns_manager: NamespaceManager) -> None:
        self.ns = ns_manager
        self.tmp_dir = Path("/tmp/vpn_research")
        self.tmp_dir.mkdir(parents=True, exist_ok=True)

    def create_interface(self, namespace: str, iface_name: str) -> None:
        """
        Creates a WireGuard virtual interface within a namespace.
        """
        logger.info(f"Operation='create_wg_interface' Namespace='{namespace}' Interface='{iface_name}'")
        self.ns.execute(namespace, ["ip", "link", "add", "dev", iface_name, "type", "wireguard"])

    def generate_and_apply_config(
        self, 
        node: VPNNodeConfiguration, 
        node_keypair: WireGuardKeyPair, 
        peer_public_keys: Dict[str, str]
    ) -> None:
        """
        Generates a WireGuard configuration file and applies it to the interface.

        Args:
            node: The VPNNodeConfiguration for the current namespace.
            node_keypair: The cryptographic keys for this specific node.
            peer_public_keys: A mapping of peer namespace names to their public keys.
        """
        conf_lines = ["[Interface]"]
        conf_lines.append(f"PrivateKey = {node_keypair.private_key}")
        
        if node.interface.listen_port:
            conf_lines.append(f"ListenPort = {node.interface.listen_port}")

        for peer in node.peers:
            conf_lines.append("\n[Peer]")
            peer_pub = peer_public_keys.get(peer.target_namespace)
            if not peer_pub:
                raise ValueError(f"Missing public key for peer: {peer.target_namespace}")
            
            conf_lines.append(f"PublicKey = {peer_pub}")
            conf_lines.append(f"AllowedIPs = {', '.join(peer.allowed_ips)}")
            
            if peer.endpoint:
                conf_lines.append(f"Endpoint = {peer.endpoint}")
            if peer.persistent_keepalive:
                conf_lines.append(f"PersistentKeepalive = {peer.persistent_keepalive}")

        conf_content = "\n".join(conf_lines)
        conf_path = self.tmp_dir / f"{node.namespace}_{node.interface.name}.conf"
        
        # Write config to /tmp (shared mount, accessible by netns)
        conf_path.write_text(conf_content, encoding="utf-8")
        # Secure the file
        os.chmod(conf_path, 0o600)

        # Apply config
        logger.info(f"Operation='apply_wg_config' Namespace='{node.namespace}'")
        self.ns.execute(
            node.namespace, 
            ["wg", "setconf", node.interface.name, str(conf_path)]
        )
        
        # Cleanup temporary config file for security
        conf_path.unlink()