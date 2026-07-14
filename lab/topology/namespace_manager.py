"""
Linux Namespace Management Layer.

Provides a robust, object-oriented abstraction over the iproute2 command-line tool 
for creating, configuring, and destroying Linux Network Namespaces.
"""

import subprocess
import logging
from dataclasses import dataclass, field
from typing import List, Optional

# Configure module-level logger
logger = logging.getLogger(__name__)
# Ensure logs contain timestamp, operation context, and namespace context
formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
if not logger.hasHandlers():
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


# --- Exceptions ---

class NamespaceError(Exception):
    """Base exception for all namespace-related operations."""
    pass


class NamespaceAlreadyExists(NamespaceError):
    """Raised when attempting to create a namespace that already exists."""
    pass


class NamespaceNotFound(NamespaceError):
    """Raised when attempting an operation on a non-existent namespace."""
    pass


class CommandExecutionError(NamespaceError):
    """Raised when a system command fails unexpectedly."""
    pass


class PermissionDenied(NamespaceError):
    """Raised when the process lacks sufficient privileges (e.g., missing sudo)."""
    pass


# --- Configuration ---

@dataclass(frozen=True, slots=True)
class LabConfig:
    """
    Configuration object defining the required namespaces for an experiment.
    
    Attributes:
        namespaces: A list of string names for the network namespaces to be provisioned.
    """
    namespaces: List[str] = field(default_factory=list)


# --- Manager ---

class NamespaceManager:
    """
    Manages the lifecycle and configuration of Linux network namespaces.
    
    This class relies on the `iproute2` suite and requires root privileges 
    to interact with the host kernel's network stack.
    """

    def __init__(self, config: LabConfig) -> None:
        """
        Initializes the NamespaceManager with a given configuration.

        Args:
            config: An instance of LabConfig defining the targeted namespaces.
            
        Example:
            >>> config = LabConfig(namespaces=["client", "router"])
            >>> manager = NamespaceManager(config)
        """
        self.config = config

    def _run_cmd(self, cmd: List[str], target_namespace: Optional[str] = None) -> subprocess.CompletedProcess:
        """
        Internal helper to execute shell commands securely.

        Args:
            cmd: A list of string arguments forming the command.
            target_namespace: Optional name of the namespace for logging context.

        Returns:
            subprocess.CompletedProcess containing stdout, stderr, and return code.

        Raises:
            PermissionDenied: If the command lacks root privileges.
            CommandExecutionError: For all other non-zero exit codes.
        """
        ns_context = target_namespace or "host"
        op_context = " ".join(cmd[:3]) if len(cmd) >= 3 else " ".join(cmd)
        
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                check=False
            )
            
            if result.returncode == 0:
                logger.debug(f"Operation='{op_context}' Namespace='{ns_context}' Status='SUCCESS'")
                return result

            # Handle explicit failures
            error_msg = result.stderr.strip() or result.stdout.strip()
            logger.error(f"Operation='{op_context}' Namespace='{ns_context}' Status='FAILURE' Details='{error_msg}'")
            
            if "Operation not permitted" in error_msg or result.returncode == 1 or result.returncode == 130:
                # 130 is common for sudo/permission drops, 1 is standard error
                if os.geteuid() != 0 if hasattr(os, 'geteuid') else False:
                     raise PermissionDenied(f"Root privileges required for: {' '.join(cmd)}")
                
            raise CommandExecutionError(f"Command failed with exit code {result.returncode}: {error_msg}")

        except FileNotFoundError:
            logger.error(f"Operation='{op_context}' Namespace='{ns_context}' Status='FAILURE' Details='Command not found'")
            raise CommandExecutionError(f"System binary not found for command: {cmd[0]}")

    def list_namespaces(self) -> List[str]:
        """
        Retrieves a list of all currently active network namespaces on the host.

        Returns:
            A list of namespace names as strings.
            
        Example:
            >>> manager.list_namespaces()
            ['client', 'gateway', 'router']
        """
        result = self._run_cmd(["ip", "netns", "list"])
        # 'ip netns list' typically outputs: "client (id: 0)\ngateway (id: 1)"
        namespaces = []
        for line in result.stdout.splitlines():
            if line.strip():
                # Extract the name before the optional (id: X) block
                name = line.split()[0]
                namespaces.append(name)
        return namespaces

    def namespace_exists(self, name: str) -> bool:
        """
        Checks if a specific network namespace exists.

        Args:
            name: The name of the namespace to check.

        Returns:
            True if it exists, False otherwise.
            
        Example:
            >>> manager.namespace_exists("client")
            True
        """
        return name in self.list_namespaces()

    def execute(self, name: str, cmd: List[str]) -> str:
        """
        Executes an arbitrary command within a specific network namespace.

        Args:
            name: The namespace in which to execute the command.
            cmd: A list of command arguments.

        Returns:
            The standard output (stdout) of the command as a string.

        Raises:
            NamespaceNotFound: If the target namespace does not exist.
            CommandExecutionError: If the command fails inside the namespace.
            
        Example:
            >>> manager.execute("client", ["ping", "-c", "1", "127.0.0.1"])
        """
        if not self.namespace_exists(name):
            raise NamespaceNotFound(f"Cannot execute command; namespace '{name}' does not exist.")
            
        full_cmd = ["ip", "netns", "exec", name] + cmd
        result = self._run_cmd(full_cmd, target_namespace=name)
        return result.stdout.strip()

    def create_namespace(self, name: str) -> None:
        """
        Creates a new isolated Linux network namespace.

        Args:
            name: The name of the namespace to create.

        Raises:
            NamespaceAlreadyExists: If a namespace with this name is already active.
            
        Example:
            >>> manager.create_namespace("vpn_server")
        """
        if self.namespace_exists(name):
            raise NamespaceAlreadyExists(f"Namespace '{name}' already exists.")
            
        self._run_cmd(["ip", "netns", "add", name], target_namespace=name)
        logger.info(f"Operation='create_namespace' Namespace='{name}' Status='SUCCESS'")

    def delete_namespace(self, name: str) -> None:
        """
        Deletes a network namespace and implicitly destroys all virtual 
        interfaces contained within it.

        Args:
            name: The name of the namespace to delete.

        Raises:
            NamespaceNotFound: If the target namespace does not exist.
            
        Example:
            >>> manager.delete_namespace("vpn_server")
        """
        if not self.namespace_exists(name):
            raise NamespaceNotFound(f"Cannot delete; namespace '{name}' does not exist.")
            
        self._run_cmd(["ip", "netns", "delete", name], target_namespace=name)
        logger.info(f"Operation='delete_namespace' Namespace='{name}' Status='SUCCESS'")

    def bring_loopback_up(self, name: str) -> None:
        """
        Activates the loopback ('lo') interface within a namespace. 
        Required for localized socket routing inside the isolated stack.

        Args:
            name: The target namespace.
            
        Example:
            >>> manager.bring_loopback_up("client")
        """
        self.execute(name, ["ip", "link", "set", "lo", "up"])
        logger.info(f"Operation='bring_loopback_up' Namespace='{name}' Status='SUCCESS'")

    def enable_ipv4_forwarding(self, name: str) -> None:
        """
        Configures the namespace kernel parameters to route IPv4 packets 
        between its interfaces (acts as a router/gateway).

        Args:
            name: The target namespace.
            
        Example:
            >>> manager.enable_ipv4_forwarding("router")
        """
        self.execute(name, ["sysctl", "-w", "net.ipv4.ip_forward=1"])
        logger.info(f"Operation='enable_ipv4_forwarding' Namespace='{name}' Status='SUCCESS'")

    def disable_ipv4_forwarding(self, name: str) -> None:
        """
        Disables IPv4 routing/forwarding within the namespace (acts as a host).

        Args:
            name: The target namespace.
            
        Example:
            >>> manager.disable_ipv4_forwarding("client")
        """
        self.execute(name, ["sysctl", "-w", "net.ipv4.ip_forward=0"])
        logger.info(f"Operation='disable_ipv4_forwarding' Namespace='{name}' Status='SUCCESS'")

    def cleanup(self) -> None:
        """
        Iterates through the provided LabConfig and deletes all defined namespaces.
        Ignores NamespaceNotFound errors to ensure a clean state regardless of 
        partial failures during creation.
        
        Example:
            >>> manager.cleanup()
        """
        logger.info(f"Operation='cleanup' Status='STARTED' TargetCount='{len(self.config.namespaces)}'")
        for ns in self.config.namespaces:
            try:
                self.delete_namespace(ns)
            except NamespaceNotFound:
                logger.debug(f"Operation='cleanup' Namespace='{ns}' Status='SKIPPED' Details='Not Found'")
        logger.info("Operation='cleanup' Status='SUCCESS'")