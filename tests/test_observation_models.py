"""
Unit tests for the Observation Framework data layer.
"""

import pytest
from framework.observation.models import (
    PacketMetadata,
    FlowMetadata,
    PacketStatistics,
)
from framework.observation.types import (
    Protocol,
    Direction,
    PacketType,
    FlowState,
)


def test_packet_metadata_immutability():
    """Ensure PacketMetadata behaves as a strictly frozen dataclass."""
    packet = PacketMetadata(
        timestamp=1630000000.123,
        length=64,
        interface="eth0",
        direction=Direction.INGRESS,
        protocol=Protocol.TCP,
        src_ip="192.168.1.100",
        dst_ip="10.0.0.1",
        packet_type=PacketType.PLAINTEXT_PROBE,
        src_port=12345,
        dst_port=80,
    )

    with pytest.raises(AttributeError):
        packet.length = 128  # type: ignore


def test_packet_flow_id_generation():
    """Ensure flow_id generates identical hashes for bidirectional traffic."""
    packet_forward = PacketMetadata(
        timestamp=1.0,
        length=100,
        interface="eth0",
        direction=Direction.EGRESS,
        protocol=Protocol.TCP,
        src_ip="192.168.1.10",
        dst_ip="1.1.1.1",
        packet_type=PacketType.PLAINTEXT_PROBE,
        src_port=55555,
        dst_port=443,
    )

    packet_reverse = PacketMetadata(
        timestamp=1.1,
        length=100,
        interface="eth0",
        direction=Direction.INGRESS,
        protocol=Protocol.TCP,
        src_ip="1.1.1.1",
        dst_ip="192.168.1.10",
        packet_type=PacketType.PLAINTEXT_PROBE,
        src_port=443,
        dst_port=55555,
    )

    assert packet_forward.flow_id == packet_reverse.flow_id


def test_flow_metadata_initialization():
    """Verify FlowMetadata defaults and standard instantiation."""
    stats = PacketStatistics(total_packets=10, total_bytes=1000)
    flow = FlowMetadata(
        flow_id="abc123hash",
        protocol=Protocol.TCP,
        state=FlowState.ESTABLISHED,
        start_time=100.0,
        end_time=105.0,
        client_ip="10.0.0.2",
        server_ip="8.8.8.8",
        stats=stats
    )

    assert flow.state == FlowState.ESTABLISHED
    assert flow.stats.total_packets == 10