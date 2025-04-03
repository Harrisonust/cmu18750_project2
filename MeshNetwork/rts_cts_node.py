import time
import board
import digitalio
from adafruit_rfm9x import RFM9x
from proj_config import NODE_ID
import adafruit_logging as logging

class RTS_CTS_Error():
    SUCCESS         = 0
    PACKAGE_CORRUPT = 1
    RTS_WRONG       = 2
    RTS_TIMEOUT     = 3
    CTS_WRONG       = 4
    CTS_TIMEOUT     = 5
    ACK_WRONG       = 6
    ACK_TIMEOUT     = 7

class RTS_CTS_NODE(RFM9x):
    # A single RTS/CTS node for the mesh network

    def __init__(self):
        self.logger = logging.getLogger('test')
        self.logger.setLevel(logging.ERROR)
        
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

    def send_raw(self, dest, control:bytes=None, payload:bytes=None) -> None:
        data = b""
        if control is not None:
            data += control
        if payload is not None:
            data += payload

        self.logger.info(f"[{self.node_id}] Sending packet from src={self.node_id} to dst={dest}, payload={payload}")
        self.send(data=data, node=self.node_id, destination=dest)

    def recv_raw(self) -> bytes:
        # self.logger.info(f"[RX {self.node_id}] Waiting for packets from other nodes")
        packet = self.receive(timeout=1, with_header=True)

        if packet is None:
            return None 
        if len(packet) > 4:
            (dest, node, packet_id, flag), payload = packet[:4], packet[4:]
            self.logger.debug(f"[{self.node_id}] Received packet from src={node} to dst={dest}, payload={payload}, snr = {self.last_snr}, rssi = {self.last_rssi}")
            return payload
        else:
            return None
    
    def send_msg(self, rx_node, payload) -> None:
        self.send_raw(dest=rx_node, control=self.CONTROL_MSG, payload=payload)
        self.num_send += 1
    
    def recv_msg(self) -> bytes:
        payload = self.recv_raw()
        if payload is None:
            return None
        
        self.num_recv += 1
        return payload[1:]

    def send_cts(self, approved_node: bytes):
        self.send_raw(dest=self.BROADCAST_ADDRESS, control=self.CONTROL_CTS+approved_node.to_bytes(1))

    def wait_cts(self) -> RTS_CTS_Error:
        ret = self.recv_raw()
        if ret is None:
            self.logger.debug(f"[{self.node_id}] cts timeout")
            return RTS_CTS_Error.CTS_TIMEOUT
        elif len(ret) != 2:
            self.logger.debug(f"[{self.node_id}] wrong cts (len(ret) != 2)")
            return RTS_CTS_Error.CTS_WRONG
            
        control1 = ret[0].to_bytes(1)  
        control2 = ret[1] # address is in int
        if control1 == self.CONTROL_CTS and control2 == self.node_id:
            self.logger.debug(f"[{self.node_id}] got cts")
            return RTS_CTS_Error.SUCCESS 
        else:
            if control1 != self.CONTROL_CTS:
                self.logger.debug(f"[{self.node_id}] wrong cts (control1 != self.CONTROL_CTS)")
            if control2 != self.node_id:
                self.logger.debug(f"[{self.node_id}] wrong cts (control2 != self.node_id)")
            return RTS_CTS_Error.CTS_WRONG
 
    def send_rts(self, request_node) -> None:
        self.send_raw(dest=request_node, control=self.CONTROL_RTS)

    def wait_rts(self) -> RTS_CTS_Error:
        ret = self.recv_raw()
        if ret is None:
            self.logger.debug(f"[{self.node_id}] rts timeout")
            return RTS_CTS_Error.RTS_TIMEOUT
        elif len(ret) != 1:
            self.logger.debug(f"[{self.node_id}] wrong rts (len(ret) != 1)")
            return RTS_CTS_Error.RTS_WRONG
        
        control = ret
        if control == self.CONTROL_RTS:
            self.logger.debug(f"[{self.node_id}] got rts")
            return RTS_CTS_Error.SUCCESS 
        else:
            self.logger.debug(f"[{self.node_id}] wrong rts (control != self.CONTROL_RTS)")
            return RTS_CTS_Error.RTS_WRONG

    def send_ack(self, tx_node) -> None:
        self.send_raw(dest=tx_node, control=self.CONTROL_ACK)
    
    def wait_ack(self) -> RTS_CTS_Error:
        ret = self.recv_raw()
        if ret is None:
            self.logger.debug(f"[{self.node_id}] act timeout")
            return RTS_CTS_Error.ACK_TIMEOUT
        elif len(ret) != 1:
            self.logger.debug(f"[{self.node_id}] wrong ack (len(ret) != 1)")
            return RTS_CTS_Error.ACK_WRONG
        
        control = ret
        if control == self.CONTROL_ACK:
            self.logger.debug(f"[{self.node_id}] got ack")
            self.num_ack += 1
            return RTS_CTS_Error.SUCCESS
        else:
            self.logger.debug(f"[{self.node_id}] wrong ack (control != self.CONTROL_ACK)")
            return RTS_CTS_Error.ACK_WRONG

    def get_stats(self):
        success_rate = f"{self.num_ack / self.num_send * 100:.2f}%" if self.num_send != 0 else "NA"
        return f"----- send:{self.num_send}/ack:{self.num_ack}/recv:{self.num_recv}/success:{success_rate} -----"
