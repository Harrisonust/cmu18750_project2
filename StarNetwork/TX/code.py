# SPDX-FileCopyrightText: 2023 Kattni Rembor for Adafruit Industries
# SPDX-License-Identifier: MIT

"""
CircuitPython Feather RP2040 RFM95 Packet Send Demo

This demo sends a "button" packet when the Boot button is pressed.

This example is meant to be paired with the Packet Receive Demo code running
on a second Feather RP2040 RFM95 board.
"""

import board
import digitalio
import keypad
import adafruit_rfm9x

# Set up button using keypad module.
button = keypad.Keys((board.BUTTON,), value_when_pressed=False)

# Define radio frequency in MHz. Must match your
# module. Can be a value like 915.0, 433.0, etc.
RADIO_FREQ_MHZ = 915.0

# Define Chip Select and Reset pins for the radio module.
CS = digitalio.DigitalInOut(board.RFM_CS)
RESET = digitalio.DigitalInOut(board.RFM_RST)

# Initialise RFM95 radio
rfm95 = adafruit_rfm9x.RFM9x(board.SPI(), CS, RESET, RADIO_FREQ_MHZ)
rfm95.node = 77
rfm95.destination = 7
rfm95.ack_retries = 5
rfm95.ack_wait = 0.5

# Set LoRa TX power and parameters
rfm95.high_power = False
rfm95.tx_power = 5

rfm95.signal_bandwidth = 500000
rfm95.spreading_factor = 12
rfm95.coding_rate = 8

while True:
    button_press = button.events.get()
    if button_press:
        if button_press.pressed:
            print(f"sending package... (src={rfm95.node}, dst={rfm95.destination})")
            if rfm95.send_with_ack(bytes("button", "UTF-8")):
                print("received ack")
            else:
                print(f"failed to receive ack (retry: {rfm95.ack_retries}, ack_timeout: {rfm95.ack_wait} sec)")
