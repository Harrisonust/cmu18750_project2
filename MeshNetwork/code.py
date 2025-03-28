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
import board_id
import time

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

# Define radio frequency in MHz
RADIO_FREQ_MHZ = 915.0

# Define Chip Select and Reset pins for the radio module.
CS = digitalio.DigitalInOut(board.RFM_CS)
RESET = digitalio.DigitalInOut(board.RFM_RST)

# Initialise RFM95 radio
rfm95 = adafruit_rfm9x.RFM9x(board.SPI(), CS, RESET, RADIO_FREQ_MHZ)

# Set node
if board_id.NODE_ID is None:
    print("please set NODE_ID in board_id.py")
nodes = [0x00, 0x01, 0x02, 0x03]
nodes.remove(board_id.NODE_ID)

# Set LoRa parameters
rfm95.signal_bandwidth = 500000
rfm95.spreading_factor = 7
rfm95.coding_rate = 8
rfm95.ack_retries = 0
rfm95.ack_wait = 3

# Counter variables
num_send = 0
num_recv = 0
num_ack  = 0

def send():
    global num_send
    global num_ack
    
    # Generate random destination
    rfm95.node = board_id.NODE_ID
    rfm95.destination = random.choice(nodes)

    # Generate random payload of colors
    color, color_name = random.choice(list(color_values.items()))

    # Debug statement
    print(f"[TX {board_id.NODE_ID}] Sending packet from src={rfm95.node} to dst={rfm95.destination}, color={color}")

    # Send the packet and see if we get an ACK back
    payload = bytes(color)
    num_send += 1
    if rfm95.send_with_ack(payload):
        print(f"[TX {board_id.NODE_ID}] Received ACK")
        num_ack += 1
        print(f"[TX {board_id.NODE_ID}] @@@ Sending color {color_name} @@@")
    else:
        print(f"[TX {board_id.NODE_ID}] Failed to receive ACK")
        

def recv():
    global num_recv
    
    # Look for a new packet - wait up to 5 seconds:
    print(f"[RX {board_id.NODE_ID}] Waiting for packets from other nodes")
    packet = rfm95.receive(timeout=3, with_header=True, with_ack=True)

    # If no packet was received during the timeout then None is returned.
    if packet is not None:
        (dest, node, packet_id, flag), payload = packet[:4], packet[4:]
        if len(payload) != 3:
            print(f"[RX {board_id.NODE_ID}] Payload corrupted {payload}")

        color = tuple(payload)        
        if color in color_values:
            color_name = color_values[color]
            print(f"[RX {board_id.NODE_ID}] Received packet from src={node} to dst={dest}, color={color}, snr = {rfm95.last_snr}, rssi = {rfm95.last_rssi}")

            # fill led color
            print(f"[RX {board_id.NODE_ID}] @@@ Changing color to {color_name} @@@")
            pixel.fill(color)
            num_recv += 1
        else: 
            print(f"[RX {board_id.NODE_ID}] Payload corrupted {payload}")



while True:
    # Based on choice, decide to TX or RX
    choice = random.randint(0, 100)

    if choice < 50:
        # Node will transmit to a random destination
        send()

    else:
        # Node will be ready to receive from other nodes
        recv()

    print(f"-----send:{num_send}/ack:{num_ack}/recv:{num_recv} -----")
