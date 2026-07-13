#!/usr/bin/env python3
"""
demo_capture.py

A complete vertical slice of the Observation Pipeline.
Captures live traffic, extracts metadata, stores to JSONL and SQLite, 
and prints real-time statistics.
"""

import time
from pathlib import Path

from framework.observation.storage import JSONLStorage, SQLiteStorage, StorageMultiplexer
from framework.observation.capture import CapturePipeline

def main() -> None:
    print("[*] Initializing VPNResearchLab Observation Pipeline...")

    # Set up output paths
    out_dir = Path("results")
    jsonl_path = out_dir / "demo_capture.jsonl"
    sqlite_path = out_dir / "demo_capture.sqlite3"

    # Initialize Storage Sinks
    print(f"[*] Setting up storage sinks at {out_dir}")
    jsonl_sink = JSONLStorage(jsonl_path)
    sqlite_sink = SQLiteStorage(sqlite_path)
    multiplexer = StorageMultiplexer([jsonl_sink, sqlite_sink])

    # Initialize the Pipeline (Capturing ALL TCP traffic for the demo)
    print("[*] Binding Capture Engine (BPF: 'tcp')")
    pipeline = CapturePipeline(
        bpf_filter="tcp",
        storage_multiplexer=multiplexer
    )

    try:
        print("[*] Starting asynchronous capture loop. Press Ctrl+C to stop.")
        pipeline.start()
        
        # Run for 10 seconds, updating the user
        for i in range(10):
            time.sleep(1)
            pipeline.print_statistics()
            
    except KeyboardInterrupt:
        print("\n[*] Capture interrupted by user.")
    finally:
        print("[*] Shutting down capture engine and flushing data to disk...")
        pipeline.stop()
        print(f"[*] Demo complete. Final count: {pipeline.packets_captured} packets.")
        print(f"    -> {jsonl_path}")
        print(f"    -> {sqlite_path}")

if __name__ == "__main__":
    main()