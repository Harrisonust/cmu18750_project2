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

        # Check return val for wait_cts()
        if flag_cts == 0x00:
            # Got a valid CTS from the dest!

            # Generate random payload of colors
            color, color_name = random.choice(list(color_values.items()))
            payload = bytes(color) + b'\x55' * 247

            # Send message to the dest and wait for an ack
            node.send_msg(payload)

        elif flag_cts == 0x01:
            # Got a CTS from another node, so channel is busy
            node_sleep()
        
        else:
            # No response from dest to the RTS
            pass

    else:
        """ ---- Node is in RX mode ---- """

        # Wait for an RTS or CTS packet
        flag_rts = node.wait_rts()

        # Check return val for wait_rts()
        if flag_rts == 0x00:
            # Got a valid RTS from a node, meant for this node!

            # Send a CTS as a broadcast to all nodes, indicating channel busy
            node.send_cts()

            # Wait for an actual message from the RTS node
            # Message will have an inbuilt ACK
            node.recv_msg()

        elif flag_rts == 0x01:
            # Got a CTS from another node, so channel is busy
            node_sleep()

        else:
            # No CTS received
            pass

    success_rate = f"{node.num_ack / node.num_send * 100:.2f}%" if node.num_send != 0 else "NA"
    print(f"----- send:{node.num_send}/ack:{node.num_ack}/recv:{node.num_recv}/success:{success_rate} -----")
