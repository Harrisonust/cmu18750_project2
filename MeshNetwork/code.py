# SPDX-FileCopyrightText: 2023 Kattni Rembor for Adafruit Industries
# SPDX-License-Identifier: MIT

"""
18750 Project 2
################
Mesh Network
"""

import board
import random
import digitalio
import neopixel
import adafruit_rfm9x
import time
from proj_config import NODE_ID

### NEOPIXEL ###
pixel = neopixel.NeoPixel(board.NEOPIXEL, 1)
pixel.brightness = 0.5
color_index = 0

color_values = {
    (255, 0, 0):    "red",
    (0, 255, 0):    "green",
    (0, 0, 255):    "blue",
    (255, 255, 0):  "yellow",
    (0, 255, 255):  "cyan",
    (255, 0, 255):  "purple",
}

# Define Chip Select and Reset pins for the radio module.
CS = digitalio.DigitalInOut(board.RFM_CS)
RESET = digitalio.DigitalInOut(board.RFM_RST)

# Initialise RFM95 radio
RADIO_FREQ_MHZ = 915.0
rfm95 = adafruit_rfm9x.RFM9x(board.SPI(), CS, RESET, RADIO_FREQ_MHZ)

# Set node
if NODE_ID is None:
    print("please set NODE_ID in proj_config.py")
    time.sleep(0xFFFFFFFF)
nodes = [0x00, 0x01, 0x02, 0x03]
nodes.remove(NODE_ID)

# Set LoRa parameters
rfm95.signal_bandwidth = 500000
rfm95.spreading_factor = 7
rfm95.coding_rate = 8
rfm95.ack_retries = 0
rfm95.ack_wait = 1

# Counter variables
num_send = 0
num_recv = 0
num_ack  = 0

while True:
    # Based on choice, decide to TX or RX
    choice = random.randint(0, 100)

    if choice < 50:
        # Node will transmit to a random destination
        send()

    else:
        # Node will be ready to receive from other nodes
        recv()

    success_rate = f"{num_ack / num_send * 100:.2f}%" if num_send != 0 else "NA"
    print(f"----- send:{num_send}/ack:{num_ack}/recv:{num_recv}/success:{success_rate} -----")
