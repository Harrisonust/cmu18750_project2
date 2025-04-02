import board
import random
import digitalio
import neopixel
import adafruit_rfm9x
import time
from proj_config import NODE_ID

class RTS_CTS_NODE:
    # A single RTS/CTS node for the mesh network

    def __init__(self):
        # Define Chip Select and Reset pins for the radio module.
        CS = digitalio.DigitalInOut(board.RFM_CS)
        RESET = digitalio.DigitalInOut(board.RFM_RST)

        # Initialise RFM95 radio
        RADIO_FREQ_MHZ = 915.0
        self.rfm95 = adafruit_rfm9x.RFM9x(board.SPI(), CS, RESET, RADIO_FREQ_MHZ)

        # Set node
        if NODE_ID is None:
            print("please set NODE_ID in proj_config.py")
            time.sleep(0xFFFFFFFF)

        self.NODE_ID = NODE_ID

        self.nodes = [0x00, 0x01, 0x02, 0x03]
        self.nodes.remove(NODE_ID)

        # Set LoRa parameters
        self.rfm95.signal_bandwidth = 500000
        self.rfm95.spreading_factor = 7
        self.rfm95.coding_rate = 8
        self.rfm95.ack_retries = 0
        self.rfm95.ack_wait = 1

        # Counter variables
        self.num_send = 0
        self.num_recv = 0
        self.num_ack  = 0

    def send_msg(self, payload):
        # Generate random destination
        self.rfm95.node = self.NODE_ID
        self.rfm95.destination = random.choice(nodes)

        # Debug statement
        print(f"[TX {self.NODE_ID}] Sending packet from src={self.rfm95.node} to dst={self.rfm95.destination}")

        self.num_send += 1

        if self.rfm95.send_with_ack(payload):
            print(f"[TX {self.NODE_ID}] Received ACK")
            self.num_ack += 1
        else:
            print(f"[TX {self.NODE_ID}] Failed to receive ACK")

    def recv_msg(self):
        # Look for a new packet
        print(f"[RX {self.NODE_ID}] Waiting for packets from other nodes")
        packet = self.rfm95.receive(timeout=1, with_header=True, with_ack=True)

        # If no packet was received during the timeout then None is returned.
        if packet is not None:
            (dest, node, packet_id, flag), payload = packet[:4], packet[4:]

            if len(payload) != 250:
                print(f"[RX {self.NODE_ID}] Payload corrupted {len(payload)=}")
                return

            print(f"[RX {self.NODE_ID}] Received packet from src={node} to dst={dest}, snr = {self.rfm95.last_snr}, rssi = {self.rfm95.last_rssi}")
            self.num_recv += 1