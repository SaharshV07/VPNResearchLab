"""
WireGuard Key Management Module.

Provides a robust abstraction for generating, deriving, storing, and validating
WireGuard cryptographic keys. Does not configure network interfaces or tunnels.
"""

import os
import subprocess
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


class WireGuardKeyError(Exception):
    """Raised when a WireGuard key operation fails."""
    pass


@dataclass(frozen=True, slots=True)
class WireGuardKeyPair:
    """Immutable representation of a WireGuard cryptographic keypair."""
    private_key: str
    public_key: str


class WireGuardKeyManager:
    """
    Manages the lifecycle of WireGuard cryptographic keys.
    
    Relies on the official 'wg' command-line utilities. Supports executing 
    key generation inside specific Linux Network Namespaces.
    """

    @staticmethod
    def _execute_wg(cmd: list[str], namespace: Optional[str] = None, stdin_data: Optional[str] = None) -> str:
        """
        Executes a WireGuard command, optionally piping standard input and 
        targeting a specific network namespace.

        Args:
            cmd: A list of command arguments (e.g., ["wg", "genkey"]).
            namespace: Optional namespace name to execute the command within.
            stdin_data: Optional string to pipe into the command's stdin.

        Returns:
            The stripped standard output of the command.

        Raises:
            WireGuardKeyError: If the command fails or the binary is missing.
        """
        full_cmd = []
        if namespace:
            full_cmd.extend(["ip", "netns", "exec", namespace])
        full_cmd.extend(cmd)

        try:
            result = subprocess.run(
                full_cmd,
                input=stdin_data,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"WireGuard command failed: {e.stderr.strip()}")
            raise WireGuardKeyError(f"Key operation failed: {e.stderr.strip()}")
        except FileNotFoundError:
            logger.error("System binary 'wg' or 'ip' not found.")
            raise WireGuardKeyError("Required system binaries not found. Is WireGuard installed?")

    def generate_private_key(self, namespace: Optional[str] = None) -> str:
        """
        Generates a new WireGuard private key using 'wg genkey'.

        Args:
            namespace: Optional namespace to execute the generation within.

        Returns:
            A base64-encoded Curve25519 private key string.
        """
        logger.debug(f"Generating private key (Namespace: {namespace or 'host'})")
        return self._execute_wg(["wg", "genkey"], namespace=namespace)

    def derive_public_key(self, private_key: str, namespace: Optional[str] = None) -> str:
        """
        Derives the corresponding public key from a given private key using 'wg pubkey'.

        Args:
            private_key: The base64-encoded private key.
            namespace: Optional namespace to execute the derivation within.

        Returns:
            A base64-encoded Curve25519 public key string.
        """
        logger.debug(f"Deriving public key (Namespace: {namespace or 'host'})")
        return self._execute_wg(["wg", "pubkey"], namespace=namespace, stdin_data=private_key)

    def generate_keypair(self, namespace: Optional[str] = None) -> WireGuardKeyPair:
        """
        Generates a complete private and public keypair.

        Args:
            namespace: Optional namespace to execute the operations within.

        Returns:
            A populated WireGuardKeyPair dataclass.
        """
        priv_key = self.generate_private_key(namespace=namespace)
        pub_key = self.derive_public_key(priv_key, namespace=namespace)
        logger.info(f"Generated new WireGuard KeyPair (Namespace: {namespace or 'host'})")
        return WireGuardKeyPair(private_key=priv_key, public_key=pub_key)

    def validate_keypair(self, keypair: WireGuardKeyPair, namespace: Optional[str] = None) -> bool:
        """
        Validates a keypair by mathematically re-deriving the public key and comparing it.

        Args:
            keypair: The WireGuardKeyPair to validate.
            namespace: Optional namespace context.

        Returns:
            True if the public key correctly corresponds to the private key, False otherwise.
        """
        try:
            expected_pub = self.derive_public_key(keypair.private_key, namespace=namespace)
            return expected_pub == keypair.public_key
        except WireGuardKeyError:
            return False

    def save_keypair(self, keypair: WireGuardKeyPair, private_path: Path, public_path: Path) -> None:
        """
        Serializes a keypair to disk. Enforces strict POSIX permissions (0o600) 
        on the private key file to prevent unauthorized access.

        Args:
            keypair: The keypair to save.
            private_path: Destination Path object for the private key.
            public_path: Destination Path object for the public key.
        """
        private_path.parent.mkdir(parents=True, exist_ok=True)
        public_path.parent.mkdir(parents=True, exist_ok=True)

        # Securely write the private key using explicit file descriptors
        flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
        mode = 0o600  # Read/Write for owner only
        
        try:
            fd = os.open(private_path, flags, mode)
            with open(fd, 'w', encoding='utf-8') as f:
                f.write(keypair.private_key + "\n")
            logger.debug(f"Saved private key to {private_path} with 0600 permissions.")
        except Exception as e:
            raise WireGuardKeyError(f"Failed to securely save private key: {e}")

        # Write the public key (Standard permissions are acceptable)
        try:
            public_path.write_text(keypair.public_key + "\n", encoding='utf-8')
            logger.debug(f"Saved public key to {public_path}.")
        except Exception as e:
            raise WireGuardKeyError(f"Failed to save public key: {e}")

    def load_keypair(self, private_path: Path, public_path: Path) -> WireGuardKeyPair:
        """
        Loads an existing keypair from disk.

        Args:
            private_path: Path to the private key file.
            public_path: Path to the public key file.

        Returns:
            The loaded WireGuardKeyPair.

        Raises:
            WireGuardKeyError: If files are missing or unreadable.
        """
        try:
            priv_key = private_path.read_text(encoding='utf-8').strip()
            pub_key = public_path.read_text(encoding='utf-8').strip()
            return WireGuardKeyPair(private_key=priv_key, public_key=pub_key)
        except FileNotFoundError as e:
            raise WireGuardKeyError(f"Key file not found: {e}")