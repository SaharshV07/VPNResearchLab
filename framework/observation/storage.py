"""
Storage Engine Module.

Provides robust sinks for storing PacketMetadata streams to JSONL and SQLite.
"""

import json
import sqlite3
from typing import List, Protocol
from pathlib import Path

from .models import PacketMetadata


class StorageBackend(Protocol):
    """Protocol defining the interface for all storage backends."""
    
    def write(self, packet: PacketMetadata) -> None:
        """Writes a single packet record to storage."""
        ...

    def close(self) -> None:
        """Safely flushes and closes the storage backend."""
        ...


class JSONLStorage:
    """
    Appends PacketMetadata to a JSON Lines file. Highly resilient to crashes.
    """

    def __init__(self, filepath: Path) -> None:
        """
        Initializes the JSONL storage backend.

        Args:
            filepath: Path to the output .jsonl file.
        """
        self.filepath = filepath
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        self._file = open(self.filepath, "a", encoding="utf-8")

    def write(self, packet: PacketMetadata) -> None:
        """Serializes and appends a packet metadata record."""
        record = packet.to_dict()
        self._file.write(json.dumps(record) + "\n")

    def close(self) -> None:
        """Closes the file handle."""
        if not self._file.closed:
            self._file.close()


class SQLiteStorage:
    """
    Stores PacketMetadata in a relational SQLite database for rapid querying.
    """

    def __init__(self, filepath: Path) -> None:
        """
        Initializes the SQLite database and schema.

        Args:
            filepath: Path to the output .sqlite3 database.
        """
        self.filepath = filepath
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.filepath, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._init_schema()

    def _init_schema(self) -> None:
        """Creates the foundational packets table if it does not exist."""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS packets (
                flow_id TEXT,
                timestamp REAL,
                length INTEGER,
                interface TEXT,
                direction TEXT,
                protocol TEXT,
                src_ip TEXT,
                dst_ip TEXT,
                packet_type TEXT,
                src_port INTEGER,
                dst_port INTEGER,
                tcp_flags TEXT,
                tcp_seq INTEGER,
                tcp_ack INTEGER,
                tcp_window INTEGER,
                ip_ttl INTEGER
            )
        """)
        self.conn.commit()

    def write(self, packet: PacketMetadata) -> None:
        """Inserts a packet metadata record into the database."""
        flags_str = "".join(packet.tcp_flags)
        
        self.cursor.execute("""
            INSERT INTO packets VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
        """, (
            packet.flow_id,
            packet.timestamp,
            packet.length,
            packet.interface,
            packet.direction.name,
            packet.protocol.name,
            packet.src_ip,
            packet.dst_ip,
            packet.packet_type.name,
            packet.src_port,
            packet.dst_port,
            flags_str,
            packet.tcp_seq,
            packet.tcp_ack,
            packet.tcp_window,
            packet.ip_ttl,
        ))
        # For a high-throughput system, commit batching is required. 
        # Kept per-packet here for demo resilience.
        self.conn.commit()

    def close(self) -> None:
        """Commits final transactions and closes the database connection."""
        self.conn.commit()
        self.conn.close()


class StorageMultiplexer:
    """
    Routes incoming packets to multiple storage backends simultaneously.
    """

    def __init__(self, backends: List[StorageBackend]) -> None:
        """
        Args:
            backends: A list of initialized storage backends.
        """
        self.backends = backends

    def write_all(self, packet: PacketMetadata) -> None:
        """Dispatches the packet to all registered backends."""
        for backend in self.backends:
            backend.write(packet)

    def close_all(self) -> None:
        """Safely closes all registered backends."""
        for backend in self.backends:
            backend.close()