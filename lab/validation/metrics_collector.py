"""
Metrics Collector Module.

Responsible for measuring baseline performance characteristics of the 
virtual network, including RTT, throughput, and interface statistics.
"""

import logging
import json
from dataclasses import dataclass
from typing import Dict, Any

from lab.topology.namespace_manager import NamespaceManager
from framework.traffic.traffic_generator import TrafficGenerator
from framework.traffic.traffic_validator import TrafficValidator

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class InterfaceStats:
    rx_bytes: int
    rx_packets: int
    tx_bytes: int
    tx_packets: int


class MetricsCollector:
    """Collects baseline metrics from the network namespaces."""

    def __init__(self, ns_manager: NamespaceManager):
        self.ns = ns_manager
        self.generator = TrafficGenerator(ns_manager, source_ns="client")

    def get_interface_statistics(self, namespace: str, interface: str) -> InterfaceStats:
        """Reads rx/tx byte and packet counts directly from the kernel sysfs."""
        try:
            base_path = f"/sys/class/net/{interface}/statistics"
            # Read stats in a single command to avoid multiple subprocess overheads
            cmd = [
                "sh", "-c", 
                f"cat {base_path}/rx_bytes {base_path}/rx_packets {base_path}/tx_bytes {base_path}/tx_packets"
            ]
            output = self.ns.execute(namespace, cmd).strip().split('\n')
            
            if len(output) == 4:
                return InterfaceStats(
                    rx_bytes=int(output[0]),
                    rx_packets=int(output[1]),
                    tx_bytes=int(output[2]),
                    tx_packets=int(output[3])
                )
        except Exception as e:
            logger.error(f"Failed to read interface statistics for {namespace}:{interface} - {e}")
            
        return InterfaceStats(0, 0, 0, 0)

    def measure_rtt(self, target_ip: str) -> float:
        """Measures Round Trip Time (RTT) in milliseconds using ICMP."""
        success, out = self.generator.generate_icmp(target_ip)
        result = TrafficValidator.validate_icmp(success, out)
        return result.latency_ms if result.success else -1.0

    def measure_throughput_mbps(self, target_ip: str, port: int = 9000) -> float:
        """
        Measures TCP throughput in Megabytes per second (MB/s).
        Connects to the TCP echo server, sends a 1MB payload, and times the return.
        """
        # Inline Python script to stream 1MB and measure the turnaround
        script = (
            "import socket, time; s=socket.socket(); s.settimeout(5); "
            f"s.connect(('{target_ip}', {port})); data=b'A'*1024*1024; "
            "t0=time.time(); s.sendall(data); recv=0; "
            "while recv < len(data): recv += len(s.recv(8192)); "
            "delta = time.time()-t0; print(f'{1.0 / delta:.2f}')"
        )
        try:
            output = self.ns.execute("client", ["python3", "-c", script]).strip()
            return float(output)
        except Exception as e:
            logger.error(f"Throughput measurement failed: {e}")
            return 0.0