"""
TCP Echo Server.

A minimal, single-threaded TCP server designed to run inside the app_server 
namespace. It receives payloads and mirrors them back to verify connection state.
"""

import socket
import sys
import logging

logging.basicConfig(level=logging.INFO, format="%(message)s")

def main(host: str, port: int) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # Allow immediate port reuse
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        s.listen(5)
        logging.info(f"TCP Echo Server listening on {host}:{port}")
        
        while True:
            try:
                conn, addr = s.accept()
                with conn:
                    data = conn.recv(1024)
                    if data:
                        conn.sendall(data)
            except KeyboardInterrupt:
                break
            except Exception as e:
                logging.error(f"TCP Error: {e}")

if __name__ == "__main__":
    host_bind = sys.argv[1] if len(sys.argv) > 1 else "0.0.0.0"
    port_bind = int(sys.argv[2]) if len(sys.argv) > 2 else 9000
    main(host_bind, port_bind)