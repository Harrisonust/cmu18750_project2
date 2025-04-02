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
from rts_cts_node import RTS_CTS_NODE

def node_sleep():
    pixel.fill(0, 0, 0)
    time.sleep(2)

### NEOPIXEL ###
pixel = neopixel.NeoPixel(board.NEOPIXEL, 1)
pixel.brightness = 0.5
color_index = 0

color_values = {
    (0, 255, 0):    "green",
    (0, 0, 255):    "blue",
    (255, 255, 0):  "yellow",
    (0, 255, 255):  "cyan",
    (255, 0, 255):  "purple",
}

node = RTS_CTS_NODE()

while True:
    # Based on choice, decide to TX or RX
    choice = random.randint(0, 100)

    if choice < 50:
        """ ---- Node is in TX mode ---- """

        # Set pixel to red for indicating TX
        pixel.fill(255, 0, 0)

        # Send RTS to random dest and wait for CTS
        node.send_rts()
        flag_cts = node.wait_cts()

        # Check if we got a CTS
        if flag_cts == 0x00:
            # Got a valid CTS from the dest!

            # Generate random payload of colors
            color, color_name = random.choice(list(color_values.items()))
            payload = bytes(color) + b'\x55' * 247

            # Send message to the dest and wait for an ack
            node.send_msg(payload)

        elif flag_cts == 0x01:
            # CTS from another node, sleep
            node_sleep()
        
        else:
            # No response from dest to the RTS
            continue

    else:
        """ ---- Node is in RX mode ---- """

        # Wait for an RTS or CTS packet
        flag_rts = node.wait_rts()

        

        pass

    success_rate = f"{num_ack / num_send * 100:.2f}%" if num_send != 0 else "NA"
    print(f"----- send:{num_send}/ack:{num_ack}/recv:{num_recv}/success:{success_rate} -----")
