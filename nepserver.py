#!/usr/bin/env python3
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime, timezone, timedelta
from os import environ

# A dictionary to hold the last values received from POST requests.
last_values = {}

class SimpleServer(BaseHTTPRequestHandler):
    def send_not_found(self):
        self.send_response(400)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"NOT FOUND\n")

    def do_GET(self):
        if self.path != "/metrics":
            self.send_not_found()
            return

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        for serial_number, value in last_values.items():
            watt = value.get("watt")
            self.wfile.write(f'nepserver_watt{{serial_number="{serial_number}"}} {watt}\n'.encode("utf-8"))

    def do_POST(self):
        if self.path != "/i.php":
            self.send_not_found()
            return

        content_length = int(self.headers.get('Content-Length'))
        post_body = self.rfile.read(content_length)
        serial_number = format(int.from_bytes(post_body[19:23], 'little'), '02x')
        watt = int(round(int.from_bytes(post_body[26:27], 'little') * 3.190))
        last_values[serial_number] = {"watt": watt}
        print(f"Receive Data from: {serial_number} watt: {watt}")

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(datetime.now(timezone(timedelta())).strftime("%Y%d%m%H%M%S").encode("utf-8"))

def run_server():
    listen_addr = environ.get("NEP_LISTEN_ADDR", "localhost")
    listen_port = int(environ.get("NEP_LISTEN_PORT", "8080"))
    web_server = HTTPServer((listen_addr, listen_port), SimpleServer)
    print(f"Server started http://{listen_addr}:{listen_port}")

    try:
        web_server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        web_server.server_close()
        print("Server stopped.")

if __name__ == "__main__":
    run_server()
