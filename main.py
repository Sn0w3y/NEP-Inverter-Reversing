#!/usr/bin/env python3
import requests
from os import environ
from urllib.parse import urljoin

class Datapoint:
    _watt_const = 3.190

    def __init__(self):
        self._serial_number = "none"
        self._watt = 0

    @staticmethod
    def parse(bytestring):
        instance = Datapoint()
        instance.serial_number = format(int.from_bytes(bytestring[19:23], 'little'), '02x')
        instance.watt = int(round(int.from_bytes(bytestring[26:27], 'little') * instance._watt_const))
        return instance

    def to_bytearray(self):
        power = int(self.watt / self._watt_const)
        sn = int(self.serial_number, 16).to_bytes(4, 'little')
        return bytes([
            # Header and static bytes
            0x79, 0x26, 0x00, 0x40, 0x14, 0x00, 0x00, 0x0f,
            0x0f, 0x0f, 0x0f, 0x00, 0x00, 0x1c, 0x00, 0xc3,
            0xc3, 0xc3, 0xc3, sn[0], sn[1], sn[2], sn[3], 0x00,
            0x00, 0x5a, power, 0x9d, 0x16, 0x80, 0x0f, 0x05,
            0x02, 0xa6, 0x31, 0xd0, 0x0a, 0x11, 0x03, 0x05,
            0x8a, 0x63, 0x17, 0xc0, 0x34
        ])

    @property
    def serial_number(self):
        return self._serial_number

    @serial_number.setter
    def serial_number(self, value):
        self._serial_number = value

    @property
    def watt(self):
        return self._watt

    @watt.setter
    def watt(self, value):
        self._watt = value

    def __str__(self):
        return f"serial_number={self.serial_number}, watt={self.watt}"

def send_data(url, dp: Datapoint):
    binary_data = dp.to_bytearray()
    headers = {'Content-Type': 'application/octet-stream'}
    response = requests.post(url, data=binary_data, headers=headers)
    return response

def main():
    base_url = environ.get('NEP_VIEWER_SERVER', 'http://www.nepviewer.net')
    url = urljoin(base_url, 'i.php')

    dp = Datapoint()
    dp.serial_number = "30c577e1"
    dp.watt = 230

    print(f'Sending data for {dp}')

    response = send_data(url, dp)

    print(f'Status code: {response.status_code}')
    print(f'Response: {response.text}')

if __name__ == "__main__":
    main()
