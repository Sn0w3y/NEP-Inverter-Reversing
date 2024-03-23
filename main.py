#!/usr/bin/env python3
import requests
from os import environ

def generate_binary_data(serial_number, watt):
    # Berechnet den Wert für das mittlere Byte basierend auf der gewünschten Leistung
    einheit_wert = 3.190
    mittleres_byte = int(watt / einheit_wert)

    # Konvertiert die Seriennummer in eine Byte-Sequenz
    serial_bytes = serial_number.to_bytes(4, 'little')

    # Erstellt die binären Daten mit dem berechneten mittleren Byte und der Seriennummer
    binary_data = bytes([
        0x79, 0x26, 0x00, 0x40, 0x14, 0x00, 0x00, 0x0f,
        0x0f, 0x0f, 0x0f, 0x00, 0x00, 0x1c, 0x00, 0xc3,

                         #-------------------------Seriennummer--------------------------#
        0xc3, 0xc3, 0xc3, serial_bytes[0], serial_bytes[1], serial_bytes[2], serial_bytes[3],

        #----V-AC---#,    #---P-AC----#
        0x00, 0x00, 0x5a, mittleres_byte, 0x9d, 0x16, 0x80, 0x0f, 0x05,
        0x02, 0xa6, 0x31, 0xd0, 0x0a, 0x11, 0x03, 0x05,
        0x8a, 0x63, 0x17, 0xc0, 0x34
    ])

    return binary_data


def send_data(url, serial_number, watt):
    binary_data = generate_binary_data(serial_number, watt)
    headers = {
        'Content-Type': 'application/octet-stream'
    }
    response = requests.post(url, data=binary_data, headers=headers)
    return response


# Ziel-URL
url = environ.get('NEP_VIEWER_SERVER', 'http://www.nepviewer.net')+'/i.php'

# Seriennummer und gewünschte Leistung (Watt) einstellen
serial_number = 0x30c577e1  # Seriennummer hier einstellen
watt = 230  # Gewünschte Wattzahl hier einstellen

print(f'Send for: {serial_number:x} watt: {watt}')

response = send_data(url, serial_number, watt)

print(f'Statuscode: {response.status_code}')
print(f'Antwort: {response.text}')
