"""
Capture Engine Module.

Manages asynchronous packet sniffing across interfaces or offline PCAPs.
"""

from typing import List, Optional, Callable
from scapy.sendrecv import AsyncSniffer
from scapy.packet import Packet

from .extractor import PacketExtractor
from .models import PacketMetadata
from .storage import StorageMultiplexer
from .exceptions import PacketParsingError


class CapturePipeline:
    """
    Coordinates packet capture, metadata extraction, and storage routing.
    Maintains live statistics regarding the capture session.
    """

    def __init__(
        self,
        interfaces: Optional[List[str]] = None,
        offline_pcap: Optional[str] = None,
        bpf_filter: str = "",
        storage_multiplexer: Optional[StorageMultiplexer] = None,
    ) -> None:
        """
        Initializes the capture pipeline.

        Args:
            interfaces: List of interface names to sniff (e.g., ["eth0", "tun0"]).
            offline_pcap: Path to a PCAP file for offline analysis.
            bpf_filter: Standard BPF filter string.
            storage_multiplexer: Configured multiplexer for data persistence.
        """
        self.interfaces = interfaces
        self.offline_pcap = offline_pcap
        self.bpf_filter = bpf_filter
        self.storage = storage_multiplexer
        self._sniffer: Optional[AsyncSniffer] = None
        
        # Live Statistics
        self.packets_captured: int = 0
        self.bytes_captured: int = 0
        self.errors: int = 0

    def _packet_callback(self, packet: Packet) -> None:
        """
        Internal callback triggered by Scapy for every captured packet.
        """
        try:
            # Scapy attaches 'sniffed_on' to packets captured live
            interface = getattr(packet, "sniffed_on", "offline")
            if not isinstance(interface, str):
                # Handle scapy interface objects
                interface = getattr(interface, "name", "unknown")

            metadata = PacketExtractor.extract(packet, interface=interface)
            
            # Update Live Stats
            self.packets_captured += 1
            self.bytes_captured += metadata.length
            
            # Persist Data
            if self.storage:
                self.storage.write_all(metadata)
                
        except PacketParsingError:
            self.errors += 1
        except Exception:
            self.errors += 1

    def start(self) -> None:
        """
        Starts the asynchronous sniffing loop in a background thread.
        """
        self._sniffer = AsyncSniffer(
            iface=self.interfaces,
            offline=self.offline_pcap,
            filter=self.bpf_filter,
            prn=self._packet_callback,
            store=False, # Do not store packets in memory to prevent RAM exhaustion
        )
        self._sniffer.start()

    def stop(self) -> None:
        """
        Gracefully stops the capture thread and closes storage backends.
        """
        if self._sniffer and self._sniffer.running:
            self._sniffer.stop()
            self._sniffer.join()
        
        if self.storage:
            self.storage.close_all()

    def print_statistics(self) -> None:
        """Outputs current live statistics to stdout."""
        print(f"Captured: {self.packets_captured} pkts | Volume: {self.bytes_captured} bytes | Errors: {self.errors}")