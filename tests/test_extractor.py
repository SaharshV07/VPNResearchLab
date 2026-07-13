import pytest
from scapy.layers.inet import IP, TCP
from framework.observation.extractor import PacketExtractor
from framework.observation.models import Protocol

def test_tcp_extraction():
    """Verify that a standard TCP/IP packet translates perfectly to PacketMetadata."""
    raw_pkt = IP(src="192.168.1.1", dst="10.0.0.1", ttl=64) / TCP(sport=12345, dport=80, flags="SA", seq=1000, ack=2000)
    raw_pkt.time = 1600000000.0
    
    metadata = PacketExtractor.extract(raw_pkt, interface="test_iface")
    
    assert metadata.src_ip == "192.168.1.1"
    assert metadata.dst_port == 80
    assert metadata.protocol == Protocol.TCP
    assert metadata.ip_ttl == 64
    assert metadata.tcp_seq == 1000
    assert metadata.tcp_ack == 2000
    assert "S" in metadata.tcp_flags
    assert "A" in metadata.tcp_flags
    assert metadata.length > 0