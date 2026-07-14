"""
HTTP Server.

A simple HTTP responder verifying Layer 7 TCP traffic.
Returns a basic 200 OK text response.
"""

import sys
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer

logging.basicConfig(level=logging.INFO, format="%(message)s")

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"HTTP_PAYLOAD_OK")
        
    def log_message(self, format: str, *args: any) -> None:
        pass  # Suppress default HTTP logging to keep console clean

def main(host: str, port: int) -> None:
    server = HTTPServer((host, port), SimpleHandler)
    logging.info(f"HTTP Server listening on {host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()

if __name__ == "__main__":
    host_bind = sys.argv[1] if len(sys.argv) > 1 else "0.0.0.0"
    port_bind = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
    main(host_bind, port_bind)