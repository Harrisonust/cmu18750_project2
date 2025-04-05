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

### NEOPIXEL ###
pixel = neopixel.NeoPixel(board.NEOPIXEL, 1)
pixel.brightness = 0.5
color_index = 0

color_values = {
    (0, 255, 0):    "green",
    (255, 255, 0):  "yellow",
    (0, 255, 255):  "cyan",
    (255, 0, 255):  "purple",
}
color_red = (255, 0, 0)
color_off = (0, 0, 0)

### Function for a node sleeping when channel is busy
def node_sleep():
    print("[NODE_SLEEP] Sleeping for 500 ms...")
    pixel.fill(color_off)
    time.sleep(0.5)


if __name__ == '__main__':
    while True:
        # Based on choice, decide to TX or RX
        choice = random.randint(0, 100)

        if choice < 50:
            """ ---- Node is in TX mode ---- """

            # Set pixel to red for indicating TX
            pixel.fill(color_red)

            # Send RTS to random dest and wait for CTS
            request_node = random.choice(neighbors)

            node.send_rts(request_node)
            flag_cts = node.wait_cts(request_node)

            # Check return val for wait_cts
            if flag_cts == RTS_CTS_Error.SUCCESS:
                # Got a valid CTS from the dest!

                # Generate random payload of colors
                color, color_name = random.choice(list(color_values.items()))
                payload = bytes(color) + b'\x55' * (node.MAX_PAYLOAD_LEN - len(color))

                # Send message to the dest
                node.send_msg(request_node, payload)

                # Wait for ACK (class does not use send_with_ack)\
                node.wait_ack()

            elif flag_cts == RTS_CTS_Error.CTS_NOT_DEST:
                # Got a CTS from another node, so channel is busy
                node_sleep()
            
            else:
                # No response from dest to the RTS
                pass

        else:
            """ ---- Node is in RX mode ---- """
            pixel.fill((0, 0, 255))

            # Wait for an RTS or CTS packet
            flag_rts = node.wait_rts()

            # Check return val for wait_rts
            if flag_rts == RTS_CTS_Error.SUCCESS:
                # Got a valid RTS from tx_node
                tx_node = node.last_node

                # Send a CTS as a broadcast to all nodes, indicating channel busy and specify tx_node
                node.send_cts(tx_node)

                # Wait for an actual message from tx_node
                payload = node.recv_msg(tx_node)

                # If no payload, go back to loop init
                if payload is None:
                    continue

                # Get color from payload
                print(payload)

                # ACK back to tx_node
                node.send_ack(tx_node)

            elif flag_rts == RTS_CTS_Error.RTS_WRONG:
                # Got a CTS from another node, so channel is busy
                node_sleep()

            else:
                # No CTS received
                pass

        print(node.get_stats())