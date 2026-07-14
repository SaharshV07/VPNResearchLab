"""
DNS Responder.

A minimal, raw socket-based DNS server mimicking standard UDP port 53 behavior.
It extracts the Transaction ID from the query and constructs a valid, dummy A-record 
response to prove binary datagram structure integrity.
"""

import socket
import sys
import logging

logging.basicConfig(level=logging.INFO, format="%(message)s")

def main(host: str, port: int) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        logging.info(f"DNS Server listening on {host}:{port}")
        
        while True:
            try:
                data, addr = s.recvfrom(1024)
                if len(data) >= 12:
                    # Construct valid DNS standard query response
                    # Keep TXID (bytes 0-2), set Flags to 0x8180 (No Error)
                    resp_header = data[:2] + b'\x81\x80' + data[4:6] + data[4:6] + b'\x00\x00\x00\x00'
                    # Append Original Question
                    resp = resp_header + data[12:]
                    # Append dummy Answer (A Record -> 8.8.8.8)
                    resp += b'\xc0\x0c\x00\x01\x00\x01\x00\x00\x00\x3c\x00\x04\x08\x08\x08\x08'
                    s.sendto(resp, addr)
            except KeyboardInterrupt:
                break
            except Exception as e:
                logging.error(f"DNS Error: {e}")

if __name__ == "__main__":
    host_bind = sys.argv[1] if len(sys.argv) > 1 else "0.0.0.0"
    port_bind = int(sys.argv[2]) if len(sys.argv) > 2 else 9053
    main(host_bind, port_bind)