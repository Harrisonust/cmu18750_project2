# SPDX-FileCopyrightText: 2023 Kattni Rembor for Adafruit Industries
# SPDX-License-Identifier: MIT

"""
18750 Project 2
################
Star network: RX Node 0x01
"""

import board
import digitalio
import neopixel
import adafruit_rfm9x

# Set up NeoPixel.
pixel = neopixel.NeoPixel(board.NEOPIXEL, 1)
pixel.brightness = 0.5

# NeoPixel colors.
"""
color_values = [
    (255, 0, 0),        # red
    (0, 255, 0),        # green
    (0, 0, 255),        # blue
    (255, 255, 0),      # yellow
    (0, 255, 255),      # cyan
    (255, 0, 255),      # purple
    (255, 255, 255),    # white
]
"""

# Define radio frequency in MHz.
RADIO_FREQ_MHZ = 915.0

# Define Chip Select and Reset pins for the radio module.
CS = digitalio.DigitalInOut(board.RFM_CS)
RESET = digitalio.DigitalInOut(board.RFM_RST)

# Initialise RFM95 radio
rfm95 = adafruit_rfm9x.RFM9x(board.SPI(), CS, RESET, RADIO_FREQ_MHZ)
rfm95.node = 0x01

rfm95.signal_bandwidth = 500000
rfm95.spreading_factor = 12
rfm95.coding_rate = 8

# Wait to receive packets.
print("Waiting for packets...")
while True:
    # Look for a new packet - wait up to 5 seconds:
    packet = rfm95.receive(timeout=5.0, with_header=True, with_ack=True)
    # If no packet was received during the timeout then None is returned.
    if packet is not None:
        print("Received a packet!")
        (dest, node, packet_id, flag), payload = packet[:4], packet[4:]
        print(f"({rfm95.last_snr=}, {rfm95.last_rssi=})")
        print(f"({dest=}, {node=}, {packet_id=})")

        # fill led color
        pixel.fill((payload[0], payload[1], payload[2]))
