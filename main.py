#!/usr/bin/env python3
import requests
from os import environ
from models import Datapoint


def send_data(url, dp : Datapoint):
    binary_data = dp.to_bytearray()
    headers = {
        'Content-Type': 'application/octet-stream'
    }
    response = requests.post(url, data=binary_data, headers=headers)
    return response


# Ziel-URL
url = environ.get('NEP_VIEWER_SERVER', 'http://www.nepviewer.net')+'/i.php'

# Seriennummer und gewünschte Leistung (Watt) einstellen
dp = Datapoint()
dp.serial_number = "30c577e1"  # Seriennummer hier einstellen
dp.watt = 230  # Gewünschte Wattzahl hier einstellen

print(f'Send for: {dp}')

response = send_data(url, dp)

print(f'Statuscode: {response.status_code}')
print(f'Antwort: {response.text}')
