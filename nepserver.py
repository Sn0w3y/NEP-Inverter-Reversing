#!/usr/bin/env python3
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime, timezone, timedelta
from os import environ
import json

# A dictionary to hold the last values received from POST requests.
last_values = {}

class SimpleServer(BaseHTTPRequestHandler):
    def __init__(self, mqttc, *args):
        self.mqttc = mqttc
        BaseHTTPRequestHandler.__init__(self, *args)

    def send_not_found(self):
        self.send_response(400)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"NOT FOUND\n")

    def send_data_per_mqtt(self, serial_number, data):
        if self.mqttc is None:
            return
        self.mqttc.publish(f"homeassistant/sensor/{serial_number}/watt/config", json.dumps({
            "name": f"Watt",
            "unique_id": f"mi_{serial_number}_watt",
            "state_topic": f"homeassistant/sensor/{serial_number}/watt",
            "icon": "mdi:solar-power-variant",
            "device_class": "energy",
            "unit_of_measurement": "W",
            "state_class": "measurement",
            "device": {
                "identifiers": f"mi_{serial_number}",
                "name": f"MI-{serial_number}",
                "manufacturer": "NEP",
                "model": "BDM-600",
                "sw_version": "unknown",
                "hw_version": "unknown"
            }
        }), True)
        self.mqttc.publish(f"homeassistant/sensor/{serial_number}/watt", data.get("watt"), True)
        print(f"send mqtt data for {serial_number}")
    
    def send_prometheus(self):
        self.send_response(200)
        self.send_header("Content-type", "application/openmetrics-text; version=1.0.0; charset=utf-8")
        self.end_headers()
        self.wfile.write('# HELP nepserver_watt A metric which expose the watt \n'.encode("utf-8"))
        self.wfile.write('# UNIT nepserver_watt watt\n'.encode("utf-8"))
        self.wfile.write('# TYPE nepserver_watt gauge\n'.encode("utf-8"))
        for serial_number, value in last_values.items():
            watt = float(value.get("watt"))
            self.wfile.write(f'nepserver_watt{{serial_number="{serial_number}"}} {watt}\n'.encode("utf-8"))
        self.wfile.write('# EOF\n'.encode("utf-8"))

    def send_json(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(last_values).encode("utf-8"))

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
        post_body = self.rfile.read(content_length)
        serial_number = format(int.from_bytes(post_body[19:23], 'little'), '02x')
        watt = int(round(int.from_bytes(post_body[26:27], 'little') * 3.190))
        data = {
            "watt": watt,
            "timestamp": datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')
        }
        self.send_data_per_mqtt(serial_number, data)
        # store for prometheus metrics
        last_values[serial_number] = data
        print(f"Receive Data from: {serial_number} watt: {watt}")

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

if __name__ == "__main__":
    run_server()
