#!/usr/bin/env python3
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime, timezone, timedelta
from os import environ


class MyServer(BaseHTTPRequestHandler):
  def do_POST(self):
    if self.path != "/i.php":
      self.send_response(400)
      self.send_header("Content-type", "text/html")
      self.end_headers()
      self.wfile.write(bytes("NOT FOUND\n", "utf-8"))
      return
    content_len = int(self.headers.get('Content-Length'))
    post_body = self.rfile.read(content_len)
    serial_number = int.from_bytes(post_body[19:23], 'little')
    watt = int(round(int.from_bytes(post_body[26:27], 'little')*3.190))
    print(f"recieve from: {serial_number} watt: {watt}")

    self.send_response(200)
    self.send_header("Content-type", "text/html")
    self.end_headers()
    self.wfile.write(bytes(datetime.now(timezone(timedelta())).strftime("%Y%d%m%H%M%S"), "utf-8"))

if __name__ == "__main__":        
    listenAddr = environ.get("NEP_LISTEN_ADDR", "localhost")
    listenPort = int(environ.get("NEP_LISTEN_PORT", "8080"))
    webServer = HTTPServer((listenAddr, listenPort), MyServer)
    print("Server started http://%s:%s" % (listenAddr, listenPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")
