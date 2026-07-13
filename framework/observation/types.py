"""
Type definitions and Enums for the Observation Framework.
"""

from enum import Enum, auto


class Protocol(Enum):
    """Supported Network/Transport Layer Protocols."""
    TCP = auto()
    UDP = auto()
    ICMP = auto()
    IPV4 = auto()
    IPV6 = auto()
    UNKNOWN = auto()


class Direction(Enum):
    """Direction of packet flow relative to the observation point."""
    INGRESS = auto()
    EGRESS = auto()
    UNKNOWN = auto()


class CaptureMode(Enum):
    """Execution mode for the capture subsystem."""
    LIVE = auto()
    OFFLINE_PCAP = auto()


class InterfaceType(Enum):
    """Classification of the network interface."""
    PHYSICAL = auto()
    VIRTUAL_TUN = auto()
    VIRTUAL_TAP = auto()
    VETH_PAIR = auto()
    LOOPBACK = auto()


class PacketType(Enum):
    """High-level classification of the packet purpose."""
    PLAINTEXT_PROBE = auto()
    ENCRYPTED_TUNNEL = auto()
    CONTROL = auto()
    NOISE = auto()


class FlowState(Enum):
    """TCP/UDP connection lifecycle states."""
    NEW = auto()
    ESTABLISHED = auto()
    CLOSED = auto()
    RESET = auto()
    TIMEOUT = auto()


class TunnelType(Enum):
    """Types of encrypted tunnels under test."""
    OPENVPN = auto()
    WIREGUARD = auto()
    IPSEC = auto()
    NONE = auto()


class ExperimentStatus(Enum):
    """Lifecycle status of a research experiment."""
    INITIALIZING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    ABORTED = auto()