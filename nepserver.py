#!/usr/bin/env python3
import json
import socketserver
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime, timezone, timedelta
from main import Datapoint
from dnslib import DNSRecord, DNSHeader, RR, QTYPE, A
from os import environ
import threading
import socket

# A dictionary to hold the last values received from POST requests.
last_values = {}

# Environment Variables for NEP-HTTP-Server Configuration
LISTEN_ADDR = environ.get("NEP_LISTEN_ADDR", "localhost")
LISTEN_PORT = int(environ.get("NEP_LISTEN_PORT", "8080"))

MQTT_ADDR = environ.get("NEP_MQTT_ADDR", None)
MQTT_PORT = int(environ.get("NEP_MQTT_PORT", "1883"))

# Environment Variables for MQTT Home Assistant discovery
MQTT_HA_EXPIRE = int(environ.get("NEP_MQTT_HA_EXPIRE", "3600"))
MQTT_HA_MANUFACTURER = environ.get("NEP_▍MQTT_HA_MANUFACTURER", "NEP")
MQTT_HA_MODEL = environ.get("NEP_MQTT_HA_MODEL", "BDM-800")

# Environment Variables for DNS Configuration
INTERCEPT_DOMAIN = 'www.nepviewer.net.'
RESPONSE_IP = environ.get('RESPONSE_IP', '0.0.0.0')  # IP to respond with for intercepted domain
FORWARD_DNS = environ.get('FORWARD_DNS', '8.8.8.8')  # DNS server to forward non-intercepted queries
DNS_LISTEN_ADDR = environ.get("NEP_LISTEN_ADDR", "0.0.0.0")  # IP for DNS server to listen on
DISABLE_DNS = environ.get('DISABLE_DNS', 'False').lower() in ['true', '1', 't', 'yes']

class DNSRequestHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data, socket = self.request
        request = DNSRecord.parse(data)

        reply = DNSRecord(DNSHeader(id=request.header.id, qr=1, aa=1, ra=1), q=request.q)

        if str(request.q.qname) == INTERCEPT_DOMAIN:
            # Intercept specific domain and respond with specified IP
            reply.add_answer(RR(request.q.qname, QTYPE.A, rdata=A(RESPONSE_IP), ttl=60))
        elif FORWARD_DNS.lower() not in ['', 'false', '0', 'f', 'no']:
            # Forward other DNS queries to a real DNS server
            try:
                forward_reply = DNSRecord.parse(DNSRecord.question(request.q.qname).send(FORWARD_DNS, timeout=1))
                for rr in forward_reply.rr:
                    reply.add_answer(rr)
            except Exception as e:
                print(f"Failed to forward DNS query: {e}")

        socket.sendto(reply.pack(), self.client_address)

class SimpleServer(BaseHTTPRequestHandler):
    def __init__(self, mqttc, *args):
        self._mqttc = mqttc
        BaseHTTPRequestHandler.__init__(self, *args)

    def send_not_found(self):
        self.send_response(400)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"NOT FOUND\n")

    def send_data_per_mqtt(self, dp: Datapoint, payload):
        if self._mqttc is None:
            return

        self._mqttc.publish("nepserver/payload", payload.hex())
        self._mqttc.publish(f"homeassistant/sensor/{dp.serial_number}/watt", dp.watt, True)

        serial_number_uppercase = dp.serial_number.upper()
        self._mqttc.publish(f"homeassistant/sensor/{dp.serial_number}/watt/config", json.dumps({
            "name": f"Watt",
            "unique_id": f"mi_{dp.serial_number}_watt",
            "state_topic": f"homeassistant/sensor/{dp.serial_number}/watt",
            "icon": "mdi:solar-power-variant",
            "device_class": "power",
            "unit_of_measurement": "W",
            "state_class": "measurement",
            "expire_after": MQTT_HA_EXPIRE,
            "device": {
                "identifiers": [
                    f"mi_{dp.serial_number}",
                    f"MI-{serial_number_uppercase}",
                    dp.serial_number
                ],
                "name": f"MI-{serial_number_uppercase}",
                "serial_number": serial_number_uppercase,
                "manufacturer": MQTT_HA_MANUFACTURER,
                "model": MQTT_HA_MODEL,
                "sw_version": "unknown",
                "hw_version": "unknown"
            }
        }), True)

        print(f"send mqtt data: {dp}")
    
    def send_prometheus(self):
        self.send_response(200)
        self.send_header("Content-type", "application/openmetrics-text; version=1.0.0; charset=utf-8")
        self.end_headers()
        self.wfile.write('# HELP nepserver_watt A metric which expose the watt \n'.encode("utf-8"))
        self.wfile.write('# UNIT nepserver_watt watt\n'.encode("utf-8"))
        self.wfile.write('# TYPE nepserver_watt gauge\n'.encode("utf-8"))
        for value in last_values.values():
            dp = value.get("datapoint")
            watt = float(dp.watt)
            self.wfile.write(f'nepserver_watt{{serial_number="{dp.serial_number}"}} {watt}\n'.encode("utf-8"))
        self.wfile.write('# EOF\n'.encode("utf-8"))

    def send_json(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()

        # json parser
        def output(obj):
            # e.g. payload of datapoint
            if isinstance(obj, bytes):
                return obj.hex()
            # e.g. timestamp
            if isinstance(obj, datetime):
                return obj.isoformat()
            if isinstance(obj, Datapoint):
                return dict((p, getattr(obj, p)) for p in dir(obj) if p[0] != "_" and isinstance(getattr(Datapoint, p), property))
            return obj.__dict__
        self.wfile.write(json.dumps(last_values, default=output).encode("utf-8"))

    def do_GET(self):
        if self.path == "/metrics":
            self.send_prometheus()
            return
        if self.path == "/data.json":
            self.send_json()
            return
        self.send_not_found()


    def do_POST(self):
        if self.path != "/i.php":
            self.send_not_found()
            return

        content_length = int(self.headers.get('Content-Length'))
        payload = self.rfile.read(content_length)

        dp = Datapoint().parse(payload)

        # send datapoint and payload per mqtt 
        self.send_data_per_mqtt(dp, payload)

        # store data in memory for prometheus metrics and data.json
        last_values[dp.serial_number] = {
            "timestamp": datetime.now(),
            "datapoint": dp,
            "payload": payload,
        }

        # dirty log (with payload)
        payload_str = payload.hex()
        print(f"Receive Data: {dp}, payload={payload_str}")

        # send http response
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        # body contains current timestamp in UTC
        self.wfile.write(datetime.now(timezone(timedelta())).strftime("%Y%d%m%H%M%S").encode("utf-8"))

def run_server():

    # setup mqtt
    mqttc = None
    if MQTT_ADDR is not None:
        try:
            import paho.mqtt.client as mqtt
            mqttc = mqtt.Client()
            mqttc.connect(MQTT_ADDR, MQTT_PORT, 60)
            mqttc.loop_start()
            print("connect to mqtt server")
        except:
            print("No mqtt support")

    # bootstrap handler with extra arguments (e.g. mqtt)
    def handler(*args):
        SimpleServer(mqttc, *args)
    web_server = HTTPServer((LISTEN_ADDR, LISTEN_PORT), handler)
    print(f"Server started http://{LISTEN_ADDR}:{LISTEN_PORT}")

    # start everything
    try:
        web_server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        web_server.server_close()
        if mqttc is not None:
            mqttc.loop_stop()
        print("Server stopped.")

def run_dns_server():
    if DISABLE_DNS:
        print("DNS server is disabled.")
        return
    with socketserver.ThreadingUDPServer((DNS_LISTEN_ADDR, 53), DNSRequestHandler) as server:
        print(f"Starting DNS server on {DNS_LISTEN_ADDR}...")
        server.serve_forever()

if __name__ == "__main__":
    # Start DNS server in a separate thread if not disabled
    if not DISABLE_DNS:
        dns_thread = threading.Thread(target=run_dns_server, daemon=True)
        dns_thread.start()
    run_server()
