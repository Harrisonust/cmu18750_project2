# SPDX-FileCopyrightText: 2023 Kattni Rembor for Adafruit Industries
# SPDX-License-Identifier: MIT

"""
18750 Project 2
################
Star Network: TX Node
"""

import board
import random
import digitalio
import neopixel
import adafruit_rfm9x

### NEOPIXEL ###
pixel = neopixel.NeoPixel(board.NEOPIXEL, 1)
pixel.brightness = 0.5
color_index = 0

color_values = [
    (255, 0, 0),        # red
    (0, 255, 0),        # green
    (0, 0, 255),        # blue
    (255, 255, 0),      # yellow
    (0, 255, 255),      # cyan
    (255, 0, 255),      # purple
]

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

nodes = [0x00, 0x01, 0x02, 0x03]
nodes.remove(rfm95.node)

rfm95.signal_bandwidth = 500000
rfm95.spreading_factor = 12
rfm95.coding_rate = 8

def send():
    # Generate random destination
    rfm95.destination = random.choice(nodes)

    # Generate random payload of colors
    color = random.choice(color_values)
    payload = bytes(color)

    # Debug statement
    print(f"Sending packet (src={rfm95.node}, dst={rfm95.destination}) color {payload}")

    # Send the packet and see if we get an ACK back
    if rfm95.send_with_ack(payload):
        print("Received ACK")
    else:
        print(f"Failed to receive ACK")

    print("")

def recv():
    # Look for a new packet - wait up to 5 seconds:
    print("Waiting for packets from other nodes")
    packet = rfm95.receive(timeout=5.0, with_header=True, with_ack=True)

    # If no packet was received during the timeout then None is returned.
    if packet is not None:
        (dest, node, packet_id, flag), payload = packet[:4], packet[4:]
        print(f"Received packet (src={rfm95.node}, dst={rfm95.destination}) color {payload}")
        print(f"SNR = {rfm95.last_snr}, RSSI = {rfm.last_rssi}")

        # fill led color
        pixel.fill((payload[0], payload[1], payload[2]))

    print("")


while True:
    # Based on choice, decide to TX or RX
    choice = random.randint(0, 255)

    if choice < 128:
        # Node will transmit to a random destination
        send()

    else:
        # Node will be ready to receive from other nodes
        recv()
