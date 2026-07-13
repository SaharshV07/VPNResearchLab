import json
import sqlite3
from pathlib import Path
from framework.observation.models import PacketMetadata, Protocol, Direction, PacketType
from framework.observation.storage import JSONLStorage, SQLiteStorage

def test_jsonl_storage(tmp_path: Path):
    file_path = tmp_path / "test.jsonl"
    storage = JSONLStorage(file_path)
    
    packet = PacketMetadata(
        timestamp=1.0, length=64, interface="eth0", direction=Direction.INGRESS,
        protocol=Protocol.TCP, src_ip="1.1.1.1", dst_ip="2.2.2.2", 
        packet_type=PacketType.NOISE, src_port=80, dst_port=1234
    )
    
    storage.write(packet)
    storage.close()
    
    with open(file_path, "r") as f:
        data = json.loads(f.readline())
        assert data["src_ip"] == "1.1.1.1"

def test_sqlite_storage(tmp_path: Path):
    db_path = tmp_path / "test.sqlite3"
    storage = SQLiteStorage(db_path)
    
    packet = PacketMetadata(
        timestamp=1.0, length=64, interface="eth0", direction=Direction.INGRESS,
        protocol=Protocol.TCP, src_ip="1.1.1.1", dst_ip="2.2.2.2", 
        packet_type=PacketType.NOISE, src_port=80, dst_port=1234, tcp_flags=("S",)
    )
    
    storage.write(packet)
    storage.close()
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT src_ip, tcp_flags FROM packets")
    row = cursor.fetchone()
    
    assert row[0] == "1.1.1.1"
    assert row[1] == "S"