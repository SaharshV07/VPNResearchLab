"""
Observation Framework Initialization.

Exposes the core data models, types, exceptions, and constants used throughout
the VPNResearchLab observation pipeline.
"""

from .types import (
    Protocol,
    Direction,
    CaptureMode,
    InterfaceType,
    PacketType,
    FlowState,
    TunnelType,
    ExperimentStatus,
)
from .models import (
    PacketMetadata,
    FlowMetadata,
    CaptureSession,
    ExperimentMetadata,
    ObservationResult,
    PacketStatistics,
    FlowStatistics,
)
from .exceptions import (
    ObservationError,
    CaptureInitializationError,
    PacketParsingError,
    FlowTrackingError,
    InvalidStateTransitionError,
)
from .constants import (
    MAX_FRAME_SIZE,
    DEFAULT_PCAP_BUFFER,
    TCP_FLAG_SYN,
    TCP_FLAG_ACK,
    TCP_FLAG_RST,
    TCP_FLAG_PSH,
    TCP_FLAG_FIN,
)

__all__ = [
    "Protocol",
    "Direction",
    "CaptureMode",
    "InterfaceType",
    "PacketType",
    "FlowState",
    "TunnelType",
    "ExperimentStatus",
    "PacketMetadata",
    "FlowMetadata",
    "CaptureSession",
    "ExperimentMetadata",
    "ObservationResult",
    "PacketStatistics",
    "FlowStatistics",
    "ObservationError",
    "CaptureInitializationError",
    "PacketParsingError",
    "FlowTrackingError",
    "InvalidStateTransitionError",
    "MAX_FRAME_SIZE",
    "DEFAULT_PCAP_BUFFER",
    "TCP_FLAG_SYN",
    "TCP_FLAG_ACK",
    "TCP_FLAG_RST",
    "TCP_FLAG_PSH",
    "TCP_FLAG_FIN",
]