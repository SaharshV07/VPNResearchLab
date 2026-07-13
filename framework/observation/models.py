"""
Core immutable dataclasses defining the observation schema.
"""

import hashlib
from dataclasses import dataclass, field
from typing import Optional, Tuple

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


@dataclass(frozen=True, slots=True)
class PacketMetadata:
    """
    Immutable representation of an observed network packet.
    
    Attributes:
        timestamp: Microsecond precision epoch arrival time.
        length: Frame length in bytes.
        interface: Name of the interface where the packet was observed.
        direction: Ingress or Egress relative to the observer.
        protocol: Transport or Network protocol identifier.
        src_ip: Source IP address.
        dst_ip: Destination IP address.
        packet_type: Classification of the packet context.
        src_port: Source port (if applicable).
        dst_port: Destination port (if applicable).
        tcp_flags: Tuple of strings representing active TCP flags.
        tcp_seq: TCP Sequence number (if applicable and visible).
        tcp_ack: TCP Acknowledgement number (if applicable and visible).
        tcp_window: TCP Window size (if applicable).
        ip_ttl: IP Time-To-Live.
    """
    timestamp: float
    length: int
    interface: str
    direction: Direction
    protocol: Protocol
    src_ip: str
    dst_ip: str
    packet_type: PacketType

    src_port: Optional[int] = None
    dst_port: Optional[int] = None
    
    tcp_flags: Tuple[str, ...] = field(default_factory=tuple)
    tcp_seq: Optional[int] = None
    tcp_ack: Optional[int] = None
    tcp_window: Optional[int] = None
    
    ip_ttl: Optional[int] = None

    @property
    def flow_id(self) -> str:
        """
        Generates a deterministic hash identifier for the bidirectional 5-tuple flow.
        """
        if self.src_port and self.dst_port:
            endpoints = sorted([
                f"{self.src_ip}:{self.src_port}",
                f"{self.dst_ip}:{self.dst_port}"
            ])
        else:
            endpoints = sorted([self.src_ip, self.dst_ip])
            
        data = f"{self.protocol.name}:{endpoints[0]}:{endpoints[1]}"
        return hashlib.md5(data.encode('utf-8')).hexdigest()


@dataclass(slots=True)
class PacketStatistics:
    """Aggregated numerical statistics for a collection of packets."""
    total_packets: int = 0
    total_bytes: int = 0
    min_packet_size: int = 0
    max_packet_size: int = 0
    average_packet_size: float = 0.0


@dataclass(slots=True)
class FlowMetadata:
    """
    Stateful representation of a tracked bidirectional network flow.
    
    Attributes:
        flow_id: Deterministic hash linking packets to this flow.
        protocol: The overarching protocol of the flow.
        state: Current lifecycle state of the connection.
        start_time: Epoch timestamp of the first observed packet.
        end_time: Epoch timestamp of the most recently observed packet.
        client_ip: IP address initiating the flow.
        server_ip: IP address responding to the flow.
        stats: Aggregated packet counts and sizes.
    """
    flow_id: str
    protocol: Protocol
    state: FlowState
    start_time: float
    end_time: float
    client_ip: str
    server_ip: str
    stats: PacketStatistics = field(default_factory=PacketStatistics)


@dataclass(slots=True)
class FlowStatistics:
    """Aggregated numerical statistics representing flow populations."""
    total_flows: int = 0
    active_flows: int = 0
    closed_flows: int = 0
    reset_flows: int = 0
    timed_out_flows: int = 0


@dataclass(slots=True)
class CaptureSession:
    """
    Metadata outlining the configuration and scope of a traffic capture operation.
    """
    session_id: str
    mode: CaptureMode
    interfaces: Tuple[InterfaceType, ...]
    bpf_filter: str
    start_time: float
    end_time: Optional[float] = None
    pcap_output_path: Optional[str] = None


@dataclass(slots=True)
class ExperimentMetadata:
    """
    High-level descriptors for a distinct research experiment execution.
    """
    experiment_id: str
    name: str
    description: str
    tunnel_type: TunnelType
    status: ExperimentStatus
    start_time: float
    end_time: Optional[float] = None


@dataclass(slots=True)
class ObservationResult:
    """
    The finalized output artifact of a completed experiment.
    Binds the metadata, session parameters, and collected statistics together.
    """
    experiment: ExperimentMetadata
    capture_session: CaptureSession
    global_packet_stats: PacketStatistics
    global_flow_stats: FlowStatistics
    notes: str = ""