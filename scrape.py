from urllib.parse import urljoin
import requests
import random
import time
import os
import re


class Datapoint:
    def __init__(self, serial_number="none"):
        self._serial_number = serial_number
        self._watt = 0

    def to_bytearray(self, byte1, byte2):
        sn = int(self.serial_number, 16).to_bytes(4, 'little')
        return bytes([
            0x79, 0x26, 0x00, 0x40, 0x14, 0x00, 0x00, 0x0f,
            0x0f, 0x0f, 0x0f, 0x00, 0x00, 0x1c, 0x00, 0xc3,
            0xc3, 0xc3, 0xc3, sn[0], sn[1], sn[2], sn[3], 0x00,
            0x00, byte1, byte2, 0x9d, 0x16, 0x80, 0x0f, 0x05,
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


def scrape_wattage(url):
    response = requests.get(url)
    page_content = response.text

    pattern = r'var now = Math\.round\((\d+)\);'
    match = re.search(pattern, page_content)

    if match:
        wattage_value = match.group(1)
        return wattage_value
    else:
        print('Wattage value not found')
        return None


def send_data(url, binary_data):
    headers = {'Content-Type': 'application/octet-stream'}
    response = requests.post(url, data=binary_data, headers=headers)
    print("sending data...")
    print(response.status_code)
    print(response.text)
    return response


def main():
    base_url = os.environ.get('NEP_VIEWER_SERVER', 'http://www.nepviewer.net')
    send_url = urljoin(base_url, 'i.php')

    # Define serial numbers and corresponding scrape URLs
    devices = {
        "30c577e5": 'https://user.nepviewer.com/pv_monitor/home/index/DE_20240326_4ut4/XXXXXXXXXXXXX',
        "30c577e6": 'https://user.nepviewer.com/pv_monitor/home/index/DE_20240326_Qoqw/XXXXXXXXXXXXX'
    }

    while True:
        for serial_number, scrape_url in devices.items():
            byte1 = random.randint(0, 255)
            byte2 = random.randint(0, 255)
            dp = Datapoint(serial_number)

            for _ in range(10):
                binary_data = dp.to_bytearray(byte1, byte2)
                send_data(send_url, binary_data)

            time.sleep(1)

            wattage = scrape_wattage(scrape_url)

            if wattage is not None:
                with open('log.txt', 'a') as log_file:
                    print(f"Written datapoints to log file for {serial_number}")
                    log_file.write(f'Byte1: {byte1}, Byte2: {byte2}, Wattage: {wattage}\n')

if __name__ == "__main__":
    main()
