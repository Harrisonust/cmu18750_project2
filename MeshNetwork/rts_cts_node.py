import time
import board
import digitalio
from adafruit_rfm9x import RFM9x
from proj_config import NODE_ID
import adafruit_logging as logging

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
        self.logger = logging.getLogger('test')
        self.logger.setLevel(logging.DEBUG)
        
        # Define Chip Select and Reset pins for the radio module.
        self.CS = digitalio.DigitalInOut(board.RFM_CS)
        self.RESET = digitalio.DigitalInOut(board.RFM_RST)
        self.RADIO_FREQ_MHZ = 915.0

        # Initialise RFM95 radio
        RFM9x.__init__(self, board.SPI(), self.CS, self.RESET, self.RADIO_FREQ_MHZ)

        # Set node
        if NODE_ID is None:
            self.logger.error("please set NODE_ID in proj_config.py")
            time.sleep(0xFFFFFFFF)

        self.node_id = NODE_ID
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

        # Counter variables
        self.num_send = 0
        self.num_recv = 0
        self.num_ack  = 0

        # Last node that transmitted to us
        self.last_node = 0xFF

    def send_raw(self, dest, control:bytes=None, payload:bytes=None) -> None:
        # Send any data and log to the logger
        data = b""

        # Add control byte for message
        if control is not None:
            data += control
        else:
            raise Exception("[CRITICAL ERROR] Tried transmitting without a control byte")

        # Add payload for message, some messages may not need one
        if payload is not None:
            data += payload

        # Log info and send
        self.logger.info(f"[{self.node_id}] Sending packet from src={self.node_id} to dst={dest}")
        self.send(data=data, node=self.node_id, destination=dest)

    def recv_raw(self) -> bytes:
        # Receive any data and log to the logger
        packet = self.receive(timeout=1, with_header=True)

        if packet is None:
            # No packet received
            self.last_node = 0xFF
            return None

        if len(packet) > 4:
            # Extract RadioHead header params
            (dest, node, packet_id, flag), payload = packet[:4], packet[4:]

            if dest != self.node_id and dest != 255:
                # Packet not meant for us
                self.logger.warning(f"[{self.node_id}] Received packet not meant for us")
                print(dest, node, packet_id, flag)

                # No packet received
                self.last_node = 0xFF
                return None

            # Save the node from this transmission as the last_node
            self.last_node = node

            # Increase num_recv
            self.logger.info(f"[{self.node_id}] Received packet from src={node} to dst={dest}, snr = {self.last_snr}, rssi = {self.last_rssi}")

            return payload

        else:
            # Wrong packet received
            self.last_node = 0xFF
            return None

    def send_msg(self, rx_node, payload) -> None:
        # Send a 250 byte message to rx_node
        self.logger.info(f"[TX {self.node_id}] Sending message to {rx_node}")
        self.send_raw(dest=rx_node, control=self.CONTROL_MSG, payload=payload)
        self.num_send += 1

    def recv_msg(self, tx_node) -> bytes:
        # Receive 250 byte message from tx_node
        payload = self.recv_raw()

        # Check for a valid payload
        if payload is None:
            self.logger.warning(f"[RX {self.node_id}] Message timeout")
            return None

        # Check if the message length is correct
        if len(payload) != 250:
            self.logger.warning(f"[RX {self.node_id}] Received wrong payload (wrong len)")
            return None

        # Check if the control byte for the message is correct
        if payload[1] != self.CONTROL_MSG:
            self.logger.warning(f"[RX {self.node_id}] Received wrong payload (wrong control byte)")
            return None

        # Check if the wrong node tried transmitting to us
        if tx_node != self.last_node:
            self.logger.error(f"[RX {self.node_id}] Node that was not cleared to send sent message")
            return None

        # Message passed all checks, return payload except control byte
        self.num_recv += 1
        return payload[1:]

    def send_rts(self, request_node) -> None:
        # Send an RTS packet: control byte only
        self.logger.info(f"[TX {self.node_id}] Sending RTS to {request_node}")
        self.send_raw(dest=request_node, control=self.CONTROL_RTS)

    def wait_rts(self) -> RTS_CTS_Error:
        self.logger.info(f"[RX {self.node_id}] Waiting for a valid RTS")

        # Receive the return value from recv_raw
        ret = self.recv_raw()

        # Check for RTS timeout
        if ret is None:
            self.logger.warning(f"[RX {self.node_id}] RTS Timeout")
            return RTS_CTS_Error.RTS_TIMEOUT

        # Check for RTS format
        elif len(ret) != 1:
            self.logger.warning(f"[RX {self.node_id}] Wrong RTS format (wrong len)")
            return RTS_CTS_Error.RTS_WRONG
        
        control = ret

        # Check for RTS control byte
        if control == self.CONTROL_RTS:
            self.logger.info(f"[RX {self.node_id}] Got a valid RTS from {self.last_node}")
            return RTS_CTS_Error.SUCCESS

        else:
            self.logger.warning(f"[RX {self.node_id}] Not an RTS")
            return RTS_CTS_Error.RTS_WRONG

    def send_cts(self, approved_node: bytes):
        # Send a broadcast CTS, specifying which node is clear to send
        self.logger.info(f"[RX {self.node_id}] Sending CTS to {approved_node}")
        self.send_raw(dest=self.BROADCAST_ADDRESS, control=self.CONTROL_CTS+approved_node.to_bytes(1))

    def wait_cts(self, request_node) -> RTS_CTS_Error:
        # Receive a valid CTS from the node we sent an RTS to
        self.logger.info(f"[TX {self.node_id}] Waiting for valid CTS from {request_node}")
        ret = self.recv_raw()

        # Check for CTS timeout
        if ret is None:
            self.logger.warning(f"[TX {self.node_id}] CTS timeout")
            return RTS_CTS_Error.CTS_TIMEOUT

        elif len(ret) != 2:
            self.logger.warning(f"[TX {self.node_id}] Wrong CTS format (wrong len)")
            return RTS_CTS_Error.CTS_WRONG

        # In ret, control1 is control byte, control2 is node that is clear to send
        control1 = ret[0].to_bytes(1)

        # No bytes conversion, ret is an int list
        control2 = ret[1]

        # Check for CTS control byte and specified node in CTS
        if control1 == self.CONTROL_CTS and control2 == self.node_id:
            # Check if the node that send the CTS is request_node
            if self.last_node == request_node:
                # Got a valid CTS
                self.logger.info(f"[TX {self.node_id}] Got a valid CTS from {request_node}")
                return RTS_CTS_Error.SUCCESS

            else:
                # Weird error, a node we never tried talking to cleared us to send
                self.logger.error(f"[TX {self.node_id}] CTS not received from {request_node}")
                raise Exception("CTS from a node we never sent RTS to")

        else:
            # Check if the message even is a CTS message
            if control1 != self.CONTROL_CTS:
                self.logger.warning(f"[TX {self.node_id}] Not a CTS message")
                return RTS_CTS_Error.CTS_WRONG

            # Check if the CTS was meant for us
            if control2 != self.node_id:
                self.logger.warning(f"[TX {self.node_id}] CTS meant for a different node")
                return RTS_CTS_Error.CTS_NOT_DEST

    def send_ack(self, tx_node) -> None:
        # Send an ACK in response to a message
        self.logger.info(f"[RX {self.node_id}] Sending ACK to {tx_node}")
        self.send_raw(dest=tx_node, control=self.CONTROL_ACK)

    def wait_ack(self) -> RTS_CTS_Error:
        # After transmitting a message, wait for an ACK
        ret = self.recv_raw()

        # Check for ACK timeout
        if ret is None:
            self.logger.warning(f"TX [{self.node_id}] ACK timeout")
            return RTS_CTS_Error.ACK_TIMEOUT

        # Check for ACK format
        elif len(ret) != 1:
            self.logger.warning(f"[{self.node_id}] Wrong ACK format (wrong len)")
            return RTS_CTS_Error.ACK_WRONG
        
        control = ret

        # Check control byte for message
        if control == self.CONTROL_ACK:
            self.logger.info(f"[{self.node_id}] Got an ACK from {self.last_node}")
            self.num_ack += 1
            return RTS_CTS_Error.SUCCESS

        else:
            self.logger.warning(f"[{self.node_id}] Not an ACK")
            return RTS_CTS_Error.ACK_WRONG

    def get_stats(self):
        success_rate = f"{self.num_ack / self.num_send * 100:.2f}%" if self.num_send != 0 else "NA"
        return f"----- send:{self.num_send}/ack:{self.num_ack}/recv:{self.num_recv}/success:{success_rate} -----"
