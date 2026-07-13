"""
Static constants used across the Observation Framework.
"""

# Networking limits
MAX_FRAME_SIZE: int = 1514
JUMBO_FRAME_SIZE: int = 9000

# Buffer Defaults
DEFAULT_PCAP_BUFFER: int = 2 * 1024 * 1024  # 2MB

# Standard Timeouts (seconds)
DEFAULT_FLOW_TIMEOUT: float = 30.0
DEFAULT_DNS_TIMEOUT: float = 5.0

# TCP Flag String Representations (Scapy alignment)
TCP_FLAG_SYN: str = "S"
TCP_FLAG_ACK: str = "A"
TCP_FLAG_RST: str = "R"
TCP_FLAG_PSH: str = "P"
TCP_FLAG_FIN: str = "F"
TCP_FLAG_URG: str = "U"