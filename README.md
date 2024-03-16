# Reverse Engineering Process of NEP Inverter Data

## Overview

This repository documents the reverse engineering process of interpreting binary data sent from a NEP inverter to its monitoring portal. The goal is to understand how various operational parameters such as serial number, AC voltage (V-AC), and AC power (P-AC) are encoded in the transmitted binary data.

## Binary Data Structure

The binary data sent to the portal is structured as follows:

```python
binary_data = bytes([
    0x79, 0x26, 0x00, 0x40, 0x14, 0x00, 0x00, 0x0f,
    0x0f, 0x0f, 0x0f, 0x00, 0x00, 0x1c, 0x00, 0xc3,
    #-------------------------Seriennummer--------------------------#
    0xc3, 0xc3, 0xc3, serial_bytes[0], serial_bytes[1], serial_bytes[2], serial_bytes[3],
    #----V-AC---#    #---P-AC----#
    0x00, 0x00, 0x5a, mittleres_byte, 0x9d, 0x16, 0x80, 0x0f, 0x05,
    0x02, 0xa6, 0x31, 0xd0, 0x0a, 0x11, 0x03, 0x05,
    0x8a, 0x63, 0x17, 0xc0, 0x34
])
```

## Key Components
Serial Number: Identified by the bytes following the 0xc3, 0xc3, 0xc3, 0xc3 sequence. This unique identifier is specific to each inverter.

AC Voltage: Represented by the bytes 0x00, 0x00, 0x5a. This segment indicates the AC voltage, decoded as 230.4V (assuming the value is in millivolts).

AC Power: The mittleres_byte represents the power in watts. The exact conversion factor from the byte value to watts is determined through experimental analysis.

## Analysis Process
The reverse engineering process involved analyzing the byte sequences sent in packets from the inverter to the monitoring portal. By changing specific bytes and observing the effects on the displayed data in the portal, we were able to deduce the purpose of various segments within the packet.

## Challenges
Decoding the entire structure of the binary data requires a comprehensive understanding of the inverter's operational metrics and potentially more sophisticated analysis techniques. Some segments of the data packet remain undeciphered and could represent other operational parameters like DC voltage, current, or system status indicators.

Contribution
Contributions to further decode and understand the binary data structure are welcome. If you have insights or have conducted similar reverse engineering efforts, please feel free to contribute to this repository.
