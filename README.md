# Reverse Engineering Process of NEP Inverter Data

## Overview

This repository documents the reverse engineering process of interpreting binary data sent from a NEP inverter to its monitoring portal. Since NEP does not provide an API to the Inverter, nor it has Modbus, Serial or any other Interface the goal is to understand how various operational parameters such as serial number, AC voltage (V-AC), and AC power (P-AC) are encoded in the transmitted binary data.

## Server Overview

The Python server implemented in this project operates on HTTP and listens for GET and POST requests. It serves the following primary functions:

- **GET `/metrics`**: Responds with the latest wattage readings from all monitored inverters, formatted for easy integration with monitoring solutions (like [Prometheus](https://prometheus.io/) and [Grafana](https://grafana.com/grafana/)).
- **GET `/data.json`**: Responds an json map with the latest wattage readings from all monitored inverters with timestamp, formatted for debugging with.
- **POST `/i.php`**: Receives binary data packets from inverters, extracts operational parameters, and updates the latest readings for each inverter.

### Key Features

- **Error Handling**: Responds with a 400 Bad Request error for paths other than `/metrics`, `/data.json` and `/i.php`, indicating invalid endpoints.
- **Dynamic Data Handling**: Utilizes a dictionary to store and update wattage readings from different inverters identified by their serial numbers.
- **Simple Deployment**: Configurable via environment variables `NEP_LISTEN_ADDR` and `NEP_LISTEN_PORT` for flexible deployment.

### MQTT (for Home Assistant)
- **Simple Deployment**: Configurable via environment variables `NEP_MQTT_ADDR` and `NEP_MQTT_PORT`.
- **MQTT Topics**: The MQTT send live on every new incoming `/i.php`-request the following values on the following Topics:
  - **WATT**: `homeassistant/sensor/{serial_number}/watt` the core
- **[Home-Assistant](https://www.home-assistant.io/integrations/mqtt) ready**: it send config topics for discovery so no extra configuration is needed:
  - **watt sensor**: `homeassistant/sensor/{serial_number}/watt/config`

### Setup Server

Put your NEP inverters into your Home WiFi, create an fake DNS-Server (which response for A-Record `www.nepviewer.net` with the IP-Adress of your server).

#### Install MQTT
Install the python-library paho-mqtt (or with `apt install python3-paho-mqtt` on debian).

If you like to use **nats-server** then follow this instructions:
Download latest [nats-server](https://nats.io/download/)-binary (or us `apt install nats-server` on debian).
Edit `/etc/nats-server.conf`:
```
port: 4222
server_name: mqtt

jetstream {
        store_dir: /var/lib/nats
}

mqtt {
        port: 1883
}
```

And wait with `nats -s nats://127.0.0.1:4222 sub "homeassistant.sensor.*.watt"` till the first value cames in.

## Binary Data Structure

The binary data sent to the portal is structured as follows:

```python
binary_data = bytes([
  #------#------#------#------#------#------#------#------#
     0x79,  0x26,  0x00,  0x40,  0x14,  0x00,  0x00,  0x0f, # 8
  #------#------#------#------#------#------#------#------#
     0x0f,  0x0f,  0x0f,  0x00,  0x00,  0x1c,  0x00,  0xc3, # 8
  #------#------#------#-------SERIAL-NUMBER-------#------#
     0xc3,  0xc3,  0xc3, sn[0], sn[1], sn[2], sn[3],  0x00, # 8
  #------#-V-AC-#-P-AC-#------#------#------#------#------#
     0x00,  0x5a, power,  0x9d,  0x16,  0x80,  0x0f,  0x05, # 8
  #------#------#------#------#------#------#------#------#
     0x02,  0xa6,  0x31,  0xd0,  0x0a,  0x11,  0x03,  0x05, # 8
  #------#------#------#------#------#
     0x8a,  0x63,  0x17,  0xc0,  0x34  # 5
])
```

## Key Components
- Note: All of the Bytes are in Little Endianness afaik.

Serial Number: Identified by the bytes following the 0xc3, 0xc3, 0xc3, 0xc3 sequence. This unique identifier is specific to each inverter.

AC Voltage: Represented by the bytes 0x00, 0x5a. This segment indicates the AC voltage, decoded as 230.4V (assuming the value is in millivolts).

AC Power: The mittleres_byte represents the power in watts. The exact conversion factor from the byte value to watts is determined through experimental analysis.

## Analysis Process
The reverse engineering process involved analyzing the byte sequences sent in packets from the inverter to the monitoring portal. By changing specific bytes and observing the effects on the displayed data in the portal, we were able to deduce the purpose of various segments within the packet.

## Challenges
Decoding the entire structure of the binary data requires a comprehensive understanding of the inverter's operational metrics and potentially more sophisticated analysis techniques. Some segments of the data packet remain undeciphered and could represent other operational parameters like DC voltage, current, or system status indicators.

Contribution
Contributions to further decode and understand the binary data structure are welcome. If you have insights or have conducted similar reverse engineering efforts, please feel free to contribute to this repository.

