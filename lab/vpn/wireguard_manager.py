"""
WireGuard Manager Module.

Provides low-level orchestration for WireGuard interfaces.
Translates configuration models into temporary native wg0.conf formats
and applies them to the kernel within isolated network namespaces.
"""

import os
import logging
from pathlib import Path
from typing import Dict

from lab.topology.namespace_manager import NamespaceManager
from lab.vpn.config import VPNNodeConfiguration
from lab.vpn.key_manager import WireGuardKeyPair

logger = logging.getLogger(__name__)


class WireGuardManager:
    """Handles creation, configuration, and destruction of WireGuard interfaces."""

    def __init__(self, ns_manager: NamespaceManager) -> None:
        """
        Initializes the WireGuardManager.

        Args:
            ns_manager: The underlying NamespaceManager for executing commands.
        """
        self.ns = ns_manager
        self.tmp_dir = Path("/tmp/vpn_research")
        self.tmp_dir.mkdir(parents=True, exist_ok=True)

    def create_interface(self, namespace: str, iface_name: str) -> None:
        """
        Creates a WireGuard virtual interface within a targeted namespace.

        Args:
            namespace: The target Linux network namespace.
            iface_name: The name of the interface (e.g., 'wg0').
        """
        logger.info(f"Creating WireGuard interface '{iface_name}' in namespace '{namespace}'")
        self.ns.execute(namespace, ["ip", "link", "add", "dev", iface_name, "type", "wireguard"])

    def generate_and_apply_config(
        self,
        node: VPNNodeConfiguration,
        node_keypair: WireGuardKeyPair,
        peer_public_keys: Dict[str, str]
    ) -> None:
        """
        Generates a temporary WireGuard configuration file and applies it to the kernel.

        Args:
            node: The configuration blueprint for this node.
            node_keypair: The cryptographic keypair for this node.
            peer_public_keys: A mapping of peer namespaces to their public keys.
            
        Raises:
            ValueError: If a required peer public key is missing.
        """
        conf_lines = ["[Interface]"]
        conf_lines.append(f"PrivateKey = {node_keypair.private_key}")

        if node.interface.listen_port:
            conf_lines.append(f"ListenPort = {node.interface.listen_port}")

        for peer in node.peers:
            conf_lines.append("\n[Peer]")
            peer_pub = peer_public_keys.get(peer.target_namespace)
            if not peer_pub:
                raise ValueError(f"Missing public key for peer namespace: {peer.target_namespace}")

            conf_lines.append(f"PublicKey = {peer_pub}")
            conf_lines.append(f"AllowedIPs = {', '.join(peer.allowed_ips)}")

            if peer.endpoint:
                conf_lines.append(f"Endpoint = {peer.endpoint}")
            if peer.persistent_keepalive:
                conf_lines.append(f"PersistentKeepalive = {peer.persistent_keepalive}")

        conf_content = "\n".join(conf_lines) + "\n"
        conf_path = self.tmp_dir / f"{node.namespace}_{node.interface.name}.conf"

        # Write configuration securely to the shared /tmp filesystem
        conf_path.write_text(conf_content, encoding="utf-8")
        os.chmod(conf_path, 0o600)

        # Apply configuration via the namespace wrapper
        logger.info(f"Applying WireGuard configuration to '{node.interface.name}' in '{node.namespace}'")
        try:
            self.ns.execute(
                node.namespace,
                ["wg", "setconf", node.interface.name, str(conf_path)]
            )
        finally:
            # Ensure secure cleanup even if application fails
            if conf_path.exists():
                conf_path.unlink()