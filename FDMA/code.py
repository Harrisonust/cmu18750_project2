# SPDX-FileCopyrightText: 2023 Kattni Rembor for Adafruit Industries
# SPDX-License-Identifier: MIT

"""
18750 Project 2
################
Mesh Network
"""

import board
import random
import neopixel
import time

from proj_config import NODE_ID
from fdma_node import FDMA_Node

# Initialize Aloha node
node = FDMA_Node()

# Initialize list of neighboring nodes
neighbors = [0x00, 0x01, 0x02, 0x03]
neighbors.remove(NODE_ID)

### NEOPIXEL ###
pixel = neopixel.NeoPixel(board.NEOPIXEL, 1)
pixel.brightness = 0.5
color_index = 0

color_map = {
    (255, 0, 0):    "red",
    (0, 255, 0):    "green",
    (0, 0, 255):    "blue",
    (255, 255, 0):  "yellow",
    (0, 255, 255):  "cyan",
    (255, 0, 255):  "purple",
}

def main():
    while True:
        # Based on choice, decide to TX or RX
        choice = random.randint(0, 100)

        if choice < 50:
            # Node will transmit to a random destination
            rx_node = random.choice(neighbors)
            color, color_name = random.choice(list(color_map.items()))
            payload = bytes(color) + b'\x55' * (node.MAX_PAYLOAD_LEN - len(color))
            node.send_msg(rx_node, payload)

        else:
            # Node will be ready to receive from other nodes
            payload = node.recv_msg()
            if payload is not None:
                print(payload)
                if len(payload) < 3:
                    continue
                color = payload[:3]
                pixel.fill(tuple(color))

        print(node.get_stats())

if __name__ == '__main__':
    main()