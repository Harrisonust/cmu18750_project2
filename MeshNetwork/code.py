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

while True:
    # Based on choice, decide to TX or RX
    choice = random.randint(0, 100)

    if choice < 50:
        # Node will transmit to a random destination
        send(rfm95)

    else:
        # Node will be ready to receive from other nodes
        recv(rfm95)

    success_rate = f"{num_ack / num_send * 100:.2f}%" if num_send != 0 else "NA"
    print(f"----- send:{num_send}/ack:{num_ack}/recv:{num_recv}/success:{success_rate} -----")
