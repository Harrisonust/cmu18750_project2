# SPDX-FileCopyrightText: 2023 Kattni Rembor for Adafruit Industries
# SPDX-License-Identifier: MIT

"""
18750 Project 2
################
Star Network: TX Node
"""

import time
import board
import digitalio
import random

import adafruit_rfm9x

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

# Define radio frequency in MHz
RADIO_FREQ_MHZ = 915.0

# Define Chip Select and Reset pins for the radio module.
CS = digitalio.DigitalInOut(board.RFM_CS)
RESET = digitalio.DigitalInOut(board.RFM_RST)

# Initialise RFM95 radio
rfm95 = adafruit_rfm9x.RFM9x(board.SPI(), CS, RESET, RADIO_FREQ_MHZ)

# Set node and LoRa parameters
rfm95.node = 0x00
rfm95.ack_retries = 0

rfm95.signal_bandwidth = 500000
rfm95.spreading_factor = 12
rfm95.coding_rate = 8

def send():
    # Generate random destination
    rfm95.destination = random.randint(1, 2)

    # Generate random payload of colors
    r = random.randint(0, 255)
    g = random.randint(0, 255)
    b = random.randint(0, 255)
    payload = bytes([r, g, b])

    # Debug statement
    print(f"Sending packet (src={rfm95.node}, dst={rfm95.destination}) color ({r}, {g}, {b})")

    # Send the packet and see if we get an ACK back
    if rfm95.send_with_ack(payload):
        print("Received ACK")
    else:
        print(f"Failed to receive ACK")


while True:
    send()
    time.sleep(5)
