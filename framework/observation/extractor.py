"""
Packet Extractor Module.

Converts raw Scapy packets into deterministic PacketMetadata dataclasses.
"""

from typing import List, Optional
from scapy.packet import Packet
from scapy.layers.inet import IP, TCP, UDP, ICMP
from scapy.layers.inet6 import IPv6

from .types import Protocol, Direction, PacketType
from .models import PacketMetadata
from .exceptions import PacketParsingError


class PacketExtractor:
    """
    Stateless extractor to parse Scapy packets into strict PacketMetadata schemas.
    """

    @staticmethod
    def extract(packet: Packet, interface: str, direction: Direction = Direction.UNKNOWN) -> PacketMetadata:
        """
        Parses a Scapy packet into a PacketMetadata object.

        Args:
            packet: The raw Scapy packet.
            interface: The interface the packet was captured on.
            direction: The directional flow of the packet (if known).

        Returns:
            PacketMetadata: The strictly typed data model.

        Raises:
            PacketParsingError: If the packet lacks basic IP/IPv6 routing layers.
        """
        if IP in packet:
            l3_layer = packet[IP]
            l3_proto = Protocol.IPV4
            src_ip = l3_layer.src
            dst_ip = l3_layer.dst
            ip_ttl = l3_layer.ttl
        elif IPv6 in packet:
            l3_layer = packet[IPv6]
            l3_proto = Protocol.IPV6
            src_ip = l3_layer.src
            dst_ip = l3_layer.dst
            ip_ttl = l3_layer.hlim
        else:
            raise PacketParsingError("Packet does not contain an IPv4 or IPv6 layer.")

        # Default L4 variables
        protocol = l3_proto
        src_port: Optional[int] = None
        dst_port: Optional[int] = None
        tcp_flags: List[str] = []
        tcp_seq: Optional[int] = None
        tcp_ack: Optional[int] = None
        tcp_window: Optional[int] = None

        # Layer 4 Parsing
        if TCP in packet:
            protocol = Protocol.TCP
            l4_layer = packet[TCP]
            src_port = l4_layer.sport
            dst_port = l4_layer.dport
            tcp_seq = l4_layer.seq
            tcp_ack = l4_layer.ack
            tcp_window = l4_layer.window
            # Convert Scapy flags (e.g., 'SA') to a list of strings (['S', 'A'])
            tcp_flags = list(str(l4_layer.flags))
        elif UDP in packet:
            protocol = Protocol.UDP
            l4_layer = packet[UDP]
            src_port = l4_layer.sport
            dst_port = l4_layer.dport
        elif ICMP in packet:
            protocol = Protocol.ICMP

        timestamp = float(packet.time)
        length = len(packet)

        return PacketMetadata(
            timestamp=timestamp,
            length=length,
            interface=interface,
            direction=direction,
            protocol=protocol,
            src_ip=src_ip,
            dst_ip=dst_ip,
            packet_type=PacketType.UNKNOWN,  # To be classified by future experiment logic
            src_port=src_port,
            dst_port=dst_port,
            tcp_flags=tuple(tcp_flags),
            tcp_seq=tcp_seq,
            tcp_ack=tcp_ack,
            tcp_window=tcp_window,
            ip_ttl=ip_ttl,
        )