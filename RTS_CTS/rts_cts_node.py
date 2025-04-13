import time
import board
import digitalio
from adafruit_rfm9x import RFM9x
import adafruit_logging as logging
from proj_config import NODE_ID

class RTS_CTS_Error():
    SUCCESS         = 0  # Success in RTS or CTS
    PACKAGE_CORRUPT = 1  # Packet corrupted in transmission

    RTS_WRONG       = 2  # Incorrect RTS format
    RTS_TIMEOUT     = 3  # No RTS received

    CTS_WRONG       = 4 # Incorrect CTS format
    CTS_NOT_DEST    = 5  # CTS not from RTS destination
    CTS_TIMEOUT     = 6  # No CTS received

    ACK_WRONG       = 7  # Incorrect ACK format
    ACK_TIMEOUT     = 8  # No ACK received


class RTS_CTS_NODE(RFM9x):
    # A single RTS/CTS node for the mesh network

    def __init__(self):
        self.logger = logging.getLogger('RTS_CTS')
        self.logger.setLevel(logging.DEBUG)
        
        # Define Chip Select and Reset pins for the radio module.
        cs = digitalio.DigitalInOut(board.RFM_CS)
        reset = digitalio.DigitalInOut(board.RFM_RST)
        radio_freq_mhz = 915.0

        # Initialise RFM95 radio
        RFM9x.__init__(self, board.SPI(), cs, reset, radio_freq_mhz)

        # Set node
        if NODE_ID is None:
            self.logger.error("Please set NODE_ID in proj_config.py")
            time.sleep(0xFFFFFFFF)

        # self.node is internal to the driver, but also used for our logs
        self.node = NODE_ID
        self.BROADCAST_ADDRESS = 255

        # Set LoRa parameters
        self.signal_bandwidth = 500000
        self.spreading_factor = 7
        self.coding_rate = 8
        self.ack_retries = 0
        self.ack_wait = 1

        # control packet definition
        self.CONTROL_MSG = b'\x00'
        self.CONTROL_RTS = b'\x01'
        self.CONTROL_CTS = b'\x02'
        self.CONTROL_ACK = b'\x03'

        # Packet length definitions
        self.HEADER_LEN  = 4
        self.CONTROL_LEN = 1
        self.MAX_PAYLOAD_LEN = 249

        # header definition
        self.HEADER_DEST = 0
        self.HEADER_NODE = 1
        self.HEADER_PACKET_ID = 2
        self.HEADER_FLAG = 3

        # Counter variables
        self.num_send = 0
        self.num_recv = 0
        self.num_ack  = 0
        self.node_start_time = time.monotonic()
        self.sent_bytes = 0
        self.last_sent_bytes = 0

        # Last node that transmitted to us
        self.last_node = 255

    def send_raw(self, dest, control:bytes=None, payload:bytes=None) -> None:
        # Send any data and log to the logger
        assert control, "[CRITICAL ERROR] Tried transmitting without a control byte"

        data = control + (payload if payload else b'')

        # Log info and send
        self.send(data=data, node=self.node, destination=dest)

    def recv_raw(self) -> bytes:
        # Receive any data and log to the logger
        packet = self.receive(timeout=1, with_header=True)

        if packet is None or len(packet) <= self.HEADER_LEN:
            # No packet received or wrong packet received
            return None, None

        # Extract RadioHead header params
        self.last_node = packet[1]

        return packet[:self.HEADER_LEN], packet[self.HEADER_LEN:]

    def send_msg(self, rx_node, payload) -> None:
        # Send a 250 byte message to rx_node
        self.logger.info(f"[TX {self.node}] Sending message to {rx_node}")
        self.send_raw(dest=rx_node, control=self.CONTROL_MSG, payload=payload)
        self.num_send += 1
        self.last_sent_bytes = len(payload)

    def recv_msg(self, tx_node) -> bytes:
        # Receive 250 byte message from tx_node
        self.logger.info(f"[TX {self.node}] Waiting for message from {self.last_node}")
        header, body = self.recv_raw()

        # Check for a valid ret
        if header is None or body is None:
            self.logger.warning(f"[RX {self.node}] Message timeout")
            return None

        # Separate control and payload
        control, payload = body[:1], body[1:]

        if len(payload) > self.MAX_PAYLOAD_LEN:
            self.logger.warning(f"[RX {self.node}] Received wrong payload (wrong len)")
            return None

        # Check if the control byte for the message is correct
        if control != self.CONTROL_MSG:
            self.logger.warning(f"[RX {self.node}] Received wrong payload (wrong control byte)")
            return None

        # Check if the wrong node tried transmitting to us
        if tx_node != self.last_node:
            self.logger.error(f"[RX {self.node}] Node that was not cleared to send sent message")
            return None

        # Message passed all checks, return payload except control byte
        self.num_recv += 1
        return payload

    def send_rts(self, request_node) -> None:
        # Send an RTS packet: control byte only
        self.logger.info(f"[TX {self.node}] Sending RTS to {request_node}")
        self.send_raw(dest=request_node, control=self.CONTROL_RTS)

    def wait_rts(self) -> RTS_CTS_Error:
        self.logger.info(f"[RX {self.node}] Waiting for a valid RTS")

        # Receive the return value from recv_raw
        header, body = self.recv_raw()

        # Check for RTS timeout
        if header is None or body is None:
            self.logger.warning(f"[RX {self.node}] RTS Timeout")
            return RTS_CTS_Error.RTS_TIMEOUT

        # Check for RTS format
        elif len(body) != 1:
            self.logger.warning(f"[RX {self.node}] Wrong RTS format (wrong len)")
            return RTS_CTS_Error.RTS_WRONG
        
        control, payload = body[:1], body[1:]

        # Check for RTS control byte
        if control == self.CONTROL_RTS:
            self.logger.info(f"[RX {self.node}] Got a valid RTS from {self.last_node}")
            return RTS_CTS_Error.SUCCESS

        else:
            self.logger.warning(f"[RX {self.node}] Not an RTS")
            return RTS_CTS_Error.RTS_WRONG

    def send_cts(self, approved_node: bytes):
        # Send a broadcast CTS, specifying which node is clear to send
        self.logger.info(f"[RX {self.node}] Sending CTS to {approved_node}")
        self.send_raw(dest=self.BROADCAST_ADDRESS, control=self.CONTROL_CTS+approved_node.to_bytes(1))

    def wait_cts(self, request_node) -> RTS_CTS_Error:
        # Receive a valid CTS from the node we sent an RTS to
        self.logger.info(f"[TX {self.node}] Waiting for valid CTS from {request_node}")
        header, body = self.recv_raw()

        # Check for CTS timeout
        if header is None or body is None:
            self.logger.warning(f"[TX {self.node}] CTS timeout")
            return RTS_CTS_Error.CTS_TIMEOUT

        elif len(body) != 2:
            self.logger.warning(f"[TX {self.node}] Wrong CTS format (wrong len)")
            return RTS_CTS_Error.CTS_WRONG

        control, payload = body[:2], body[2:]

        # In ret, control1 is control byte, control2 is node that is clear to send
        control1 = control[0].to_bytes(1)

        # No bytes conversion, ret is an int list
        control2 = control[1]

        # Check for CTS control byte and specified node in CTS
        if control1 == self.CONTROL_CTS and control2 == self.node:
            # Check if the node that send the CTS is request_node
            if self.last_node == request_node:
                # Got a valid CTS
                self.logger.info(f"[TX {self.node}] Got a valid CTS from {request_node}")
                return RTS_CTS_Error.SUCCESS

            else:
                # Weird error, a node we never tried talking to cleared us to send
                self.logger.error(f"[TX {self.node}] CTS not received from {request_node}")
                raise Exception("CTS from a node we never sent RTS to")

        else:
            # Check if the message even is a CTS message
            if control1 != self.CONTROL_CTS:
                self.logger.warning(f"[TX {self.node}] Not a CTS message")
                return RTS_CTS_Error.CTS_WRONG

            # Check if the CTS was meant for us
            if control2 != self.node:
                self.logger.warning(f"[TX {self.node}] CTS meant for a different node")
                return RTS_CTS_Error.CTS_NOT_DEST

    def send_ack(self, tx_node) -> None:
        # Send an ACK in response to a message
        self.logger.info(f"[RX {self.node}] Sending ACK to {tx_node}")
        self.send_raw(dest=tx_node, control=self.CONTROL_ACK)

    def wait_ack(self) -> RTS_CTS_Error:
        # After transmitting a message, wait for an ACK
        self.logger.info(f"[TX {self.node}] Waiting for valid ACK from {self.last_node}")
        header, body = self.recv_raw()

        # Check for ACK timeout
        if header is None or body is None:
            self.logger.warning(f"TX [{self.node}] ACK timeout")
            return RTS_CTS_Error.ACK_TIMEOUT

        # Check for ACK format
        elif len(body) != 1:
            self.logger.warning(f"[{self.node}] Wrong ACK format (wrong len)")
            return RTS_CTS_Error.ACK_WRONG
        
        control, payload = body[:1], body[1:]

        # Check control byte for message
        if control == self.CONTROL_ACK:
            self.logger.info(f"[{self.node}] Got an ACK from {self.last_node}")
            self.sent_bytes += self.last_sent_bytes
            self.num_ack += 1
            return RTS_CTS_Error.SUCCESS

        else:
            self.logger.warning(f"[{self.node}] Not an ACK")
            return RTS_CTS_Error.ACK_WRONG

    def get_stats(self):
        time_elapsed = time.monotonic() - self.node_start_time
        throughput = self.sent_bytes * 8 / time_elapsed # in bps
        success_rate = f"{self.num_ack / self.num_send * 100:.2f}%" if self.num_send else "NA"
        return f"----- send:{self.num_send}/ack:{self.num_ack}/recv:{self.num_recv}/success:{success_rate}/throughput:{throughput:.2f}bps -----"
