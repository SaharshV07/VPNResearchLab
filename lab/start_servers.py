"""
Service Orchestrator.

Deploys the Python listener services into the target app_server namespace 
as asynchronous background processes.
"""

import subprocess
import logging
from typing import List
from pathlib import Path

logger = logging.getLogger(__name__)

class ServiceOrchestrator:
    """Manages background server processes inside a namespace."""

    def __init__(self, target_ns: str):
        self.target_ns = target_ns
        self.processes: List[subprocess.Popen] = []
        self.base_dir = Path(__file__).resolve().parent.parent / "framework" / "traffic"

    def start_all(self) -> None:
        """Spawns HTTP, TCP, UDP, and DNS listeners."""
        servers = [
            ("http_server.py", "8000"),
            ("tcp_echo.py", "9000"),
            ("udp_echo.py", "9001"),
            ("dns_server.py", "9053"),
        ]

        logger.info(f"Starting target services in namespace: {self.target_ns}")
        for script, port in servers:
            script_path = str(self.base_dir / script)
            cmd = ["ip", "netns", "exec", self.target_ns, "python3", script_path, "0.0.0.0", port]
            
            # Launch detached background process
            proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.processes.append(proc)
            logger.info(f" -> {script} (Port {port}) started [PID: {proc.pid}]")

    def stop_all(self) -> None:
        """Terminates all spawned processes."""
        logger.info("Terminating all background services...")
        for proc in self.processes:
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()