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
from rts_cts_node import RTS_CTS_NODE, RTS_CTS_Error

# Initialize RTS-CTS node
node = RTS_CTS_NODE()

# Initialize list of neighboring nodes
neighbors = [0x00, 0x01, 0x02, 0x03]
neighbors.remove(NODE_ID)

# Node we are currently trying to transmit to
request_node = 0xFF

# Node currently trying to transmit to us
receive_node = 0xFF

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


# Function for a node sleeping when channel is busy
def node_sleep():
    pixel.fill(0, 0, 0)
    time.sleep(2)


if __name__ == '__main__':
        while True:
        # Based on choice, decide to TX or RX
        choice = random.randint(0, 100)

        if choice < 50:
            """ ---- Node is in TX mode ---- """

            # Set pixel to red for indicating TX
            pixel.fill(255, 0, 0)

            # Send RTS to random dest and wait for CTS
            request_node = random.choice(neighbors)

            node.send_rts(request_node)
            flag_cts = node.wait_cts()

            # Check return val for wait_cts()
            if flag_cts == RTS_CTS_Error.SUCCESS:
                # Got a valid CTS from the dest!

                # Generate random payload of colors
                color, color_name = random.choice(list(color_values.items()))
                payload = bytes(color) + b'\x55' * 247

                # Send message to the dest and wait for an ack
                node.send_msg(payload)

            elif flag_cts == RTS_CTS_Error.CTS_WRONG:
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
            if flag_rts == RTS_CTS_Error.SUCCESS:
                # Got a valid RTS from a node, meant for this node!

                # Send a CTS as a broadcast to all nodes, indicating channel busy
                node.send_cts()

                # Wait for an actual message from the RTS node
                # Message will have an inbuilt ACK
                node.recv_msg()

            elif flag_rts == RTS_CTS_Error.RTS_WRONG:
                # Got a CTS from another node, so channel is busy
                node_sleep()

            else:
                # No CTS received
                pass

        print(node.get_stats())