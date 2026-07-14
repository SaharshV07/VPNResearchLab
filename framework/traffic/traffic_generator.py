"""
Traffic Generator.

Executes client-side traffic generation commands from within the designated namespace.
Uses inline Python scripts for TCP/UDP/DNS to ensure compatibility without requiring
external packages like netcat or dnsutils in the virtual stack.
"""

from typing import Tuple
from lab.topology.namespace_manager import NamespaceManager, CommandExecutionError

class TrafficGenerator:
    """Generates synthetic traffic for specific protocols."""

    def __init__(self, manager: NamespaceManager, source_ns: str):
        self.manager = manager
        self.source_ns = source_ns

    def _execute(self, cmd: list) -> Tuple[bool, str]:
        """Runs a command and returns (success_bool, stdout/stderr)."""
        try:
            output = self.manager.execute(self.source_ns, cmd)
            return True, output.strip()
        except CommandExecutionError as e:
            return False, str(e)

    def generate_icmp(self, target_ip: str) -> Tuple[bool, str]:
        """Generates an ICMP Echo Request."""
        cmd = ["ping", "-c", "1", "-W", "1", target_ip]
        return self._execute(cmd)

    def generate_tcp(self, target_ip: str, port: int, payload: str = "TCP_TEST") -> Tuple[bool, str]:
        """Generates a TCP socket payload and awaits the echo."""
        script = (
            "import socket, time; t=time.time(); s=socket.socket(); s.settimeout(2); "
            f"s.connect(('{target_ip}', {port})); s.sendall(b'{payload}'); "
            "print(f'{time.time()-t}|{s.recv(1024).decode()}')"
        )
        return self._execute(["python3", "-c", script])

    def generate_udp(self, target_ip: str, port: int, payload: str = "UDP_TEST") -> Tuple[bool, str]:
        """Generates a UDP datagram and awaits the echo."""
        script = (
            "import socket, time; t=time.time(); s=socket.socket(2, 2); s.settimeout(2); "
            f"s.sendto(b'{payload}', ('{target_ip}', {port})); "
            "print(f'{time.time()-t}|{s.recvfrom(1024)[0].decode()}')"
        )
        return self._execute(["python3", "-c", script])

    def generate_http(self, target_ip: str, port: int) -> Tuple[bool, str]:
        """Generates an HTTP GET request."""
        script = (
            "import urllib.request, time; t=time.time(); "
            f"r=urllib.request.urlopen('http://{target_ip}:{port}', timeout=2); "
            "print(f'{time.time()-t}|{r.read().decode()}')"
        )
        return self._execute(["python3", "-c", script])

    def generate_dns(self, target_ip: str, port: int) -> Tuple[bool, str]:
        """Generates a binary DNS query and parses the transaction ID return."""
        script = (
            "import socket, time; t=time.time(); s=socket.socket(2, 2); s.settimeout(2); "
            "req=b'\\xaa\\xbb\\x01\\x00\\x00\\x01\\x00\\x00\\x00\\x00\\x00\\x00\\x04test\\x03com\\x00\\x00\\x01\\x00\\x01'; "
            f"s.sendto(req, ('{target_ip}', {port})); resp=s.recv(1024); "
            "success='OK' if resp[:2]==b'\\xaa\\xbb' else 'FAIL'; "
            "print(f'{time.time()-t}|{success}')"
        )
        return self._execute(["python3", "-c", script])