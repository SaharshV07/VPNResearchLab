"""
UDP Echo Server.

A minimal stateless UDP server. Receives datagrams and returns them to the 
sender to verify Layer 4 UDP routing and NAT traversal states.
"""

import socket
import sys
import logging

logging.basicConfig(level=logging.INFO, format="%(message)s")

def main(host: str, port: int) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        logging.info(f"UDP Echo Server listening on {host}:{port}")
        
        while True:
            try:
                data, addr = s.recvfrom(1024)
                if data:
                    s.sendto(data, addr)
            except KeyboardInterrupt:
                break
            except Exception as e:
                logging.error(f"UDP Error: {e}")

if __name__ == "__main__":
    host_bind = sys.argv[1] if len(sys.argv) > 1 else "0.0.0.0"
    port_bind = int(sys.argv[2]) if len(sys.argv) > 2 else 9001
    main(host_bind, port_bind)