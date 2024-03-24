#!/usr/bin/env python3
import json
import socketserver
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime, timezone, timedelta
from models import Datapoint
from dnslib import DNSRecord, DNSHeader, RR, QTYPE, A
from os import environ
import threading
import socket

# A dictionary to hold the last values received from POST requests.
last_values = {}

# Environment Variables for DNS Configuration
INTERCEPT_DOMAIN = 'www.nepviewer.net/i.php'
RESPONSE_IP = environ.get('RESPONSE_IP', '127.0.0.1')  # IP to respond with for intercepted domain
FORWARD_DNS = environ.get('FORWARD_DNS', '8.8.8.8')    # DNS server to forward non-intercepted queries

class DNSRequestHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data, socket = self.request
        request = DNSRecord.parse(data)

        reply = DNSRecord(DNSHeader(id=request.header.id, qr=1, aa=1, ra=1), q=request.q)

        if str(request.q.qname) == INTERCEPT_DOMAIN:
            # Intercept specific domain and respond with specified IP
            reply.add_answer(RR(request.q.qname, QTYPE.A, rdata=A(RESPONSE_IP), ttl=60))
        else:
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
        self.mqttc = mqttc
        BaseHTTPRequestHandler.__init__(self, *args)

    def send_not_found(self):
        self.send_response(400)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"NOT FOUND\n")

    def send_data_per_mqtt(self, dp: Datapoint, payload):
        if self.mqttc is None:
            return
        serial_number_uppercase = dp.serial_number.upper()
        self.mqttc.publish(f"homeassistant/sensor/{dp.serial_number}/watt/config", json.dumps({
            "name": f"Watt",
            "unique_id": f"mi_{dp.serial_number}_watt",
            "state_topic": f"homeassistant/sensor/{dp.serial_number}/watt",
            "icon": "mdi:solar-power-variant",
            "device_class": "power",
            "unit_of_measurement": "W",
            "state_class": "measurement",
            "expire_after": 3600,
            "device": {
                "identifiers": [
                    f"mi_{dp.serial_number}",
                    f"MI-{serial_number_uppercase}",
                    dp.serial_number
                ],
                "name": f"MI-{serial_number_uppercase}",
                "serial_number": serial_number_uppercase,
                "manufacturer": "NEP",
                "model": "BDM-600",
                "sw_version": "unknown",
                "hw_version": "unknown"
            }
        }), True)
        self.mqttc.publish(f"homeassistant/sensor/{dp.serial_number}/watt", dp.watt, True)
        self.mqttc.publish("nepserver/payload", payload.hex())
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
        def output(obj):
            if isinstance(obj, bytes):
                return obj.hex()
            if isinstance(obj, datetime):
                return obj.isoformat()
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
        self.send_data_per_mqtt(dp, payload)
        data = {
            "timestamp": datetime.now(),
            "datapoint": dp,
            "payload": payload,
        }
        # store for prometheus metrics
        last_values[dp.serial_number] = data
        payload_str = payload.hex()
        print(f"Receive Data: {dp}, payload={payload_str}")

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(datetime.now(timezone(timedelta())).strftime("%Y%d%m%H%M%S").encode("utf-8"))

def run_server():
    listen_addr = environ.get("NEP_LISTEN_ADDR", "localhost")
    listen_port = int(environ.get("NEP_LISTEN_PORT", "8080"))

    mqtt_addr = environ.get("NEP_MQTT_ADDR", None)
    mqtt_port = int(environ.get("NEP_MQTT_PORT", "1883"))
    mqttc = None
    if mqtt_addr is not None:
        try:
            import paho.mqtt.client as mqtt
            mqttc = mqtt.Client()
            mqttc.connect(mqtt_addr, mqtt_port, 60)
            mqttc.loop_start()
            print("connect to mqtt server")
        except:
            print("No mqtt support")

    def handler(*args):
        SimpleServer(mqttc, *args)
    web_server = HTTPServer((listen_addr, listen_port), handler)
    print(f"Server started http://{listen_addr}:{listen_port}")

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
    with socketserver.ThreadingUDPServer(('0.0.0.0', 53), DNSRequestHandler) as server:
        print("Starting DNS server...")
        server.serve_forever()

if __name__ == "__main__":

    # Start DNS server in a separate thread
    dns_thread = threading.Thread(target=run_dns_server, daemon=True)
    dns_thread.start()

    run_server()
