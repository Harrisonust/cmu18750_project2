import time
import board
import digitalio
from adafruit_rfm9x import RFM9x
import adafruit_logging as logging
from proj_config import NODE_ID

class FDMA_Node(RFM9x):
    def __init__(self):
        self.logger = logging.getLogger('FDMA')
        self.logger.setLevel(logging.DEBUG)
        
        # Define Chip Select and Reset pins for the radio module.
        cs = digitalio.DigitalInOut(board.RFM_CS)
        reset = digitalio.DigitalInOut(board.RFM_RST)
        
        # Set node
        if NODE_ID is None:
            self.logger.error("Please set NODE_ID in proj_config.py")
            time.sleep(0xFFFFFFFF)

        # Initialise RFM95 radio
        RFM9x.__init__(self, board.SPI(), cs, reset, 915.0) # default freq

        self.node = NODE_ID
        self.BROADCAST_ADDRESS = 255

        # Set LoRa parameters
        self.signal_bandwidth = 500000
        self.spreading_factor = 7
        self.coding_rate = 8
        self.ack_retries = 0
        self.ack_wait = 1

        # Packet length definitions
        self.MAX_PAYLOAD_LEN = 250

        # Counter variables
        self.num_send = 0
        self.num_recv = 0
        self.num_ack  = 0
        self.node_start_time = time.monotonic()
        self.sent_bytes = 0

        # setup frequency table
        self.frequency_table = {
            0: 910, 
            1: 911,
            2: 912,
            3: 913
        }

    def send_msg(self, rx_node, payload) -> None:
        # Debug statement
        self.logger.info(f"[TX {self.node}] Sending packet from src={self.node} to dst={rx_node}")
        self.destination = rx_node
        
        # set transmitting freq to dest freq
        self.frequency_mhz = self.frequency_table[self.destination]

        # Send the packet and see if we get an ACK back
        self.num_send += 1
        if self.send_with_ack(payload):
            self.logger.info(f"[TX {self.node}] Received ACK")
            self.sent_bytes += len(payload)
            self.num_ack += 1
        else:
            self.logger.info(f"[TX {self.node}] Failed to receive ACK")

    def recv_msg(self) -> bytes:
        # Look for a new packet - wait up to 5 seconds:
        self.logger.info(f"[RX {self.node}] Waiting for packets from other nodes")

        # set receiving freq to self freq
        self.frequency_mhz = self.frequency_table[self.node]

        # receive
        packet = self.receive(timeout=3, with_header=True, with_ack=True)

        # If no packet was received during the timeout then None is returned.
        if packet is not None:
            (dest, node, packet_id, flag), payload = packet[:4], packet[4:]
            if len(payload) > self.MAX_PAYLOAD_LEN:
                self.logger.info(f"[RX {self.node}] Payload corrupted {payload}")
                return None
            else:
                self.num_recv += 1
                return payload
        return None
    
    def get_stats(self):
        time_elapsed = time.monotonic() - self.node_start_time
        throughput = self.sent_bytes * 8 / time_elapsed # in bps
        success_rate = f"{self.num_ack / self.num_send * 100:.2f}%" if self.num_send else "NA"
        return f"----- send:{self.num_send}/ack:{self.num_ack}/recv:{self.num_recv}/success:{success_rate}/throughput:{throughput:.2f}bps -----"
