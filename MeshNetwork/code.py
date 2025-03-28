import board
import digitalio
import neopixel
import adafruit_rfm9x

### NEOPIXEL ###
pixel = neopixel.NeoPixel(board.NEOPIXEL, 1)
pixel.brightness = 0.5
color_values = [
    (255, 0, 0),
    (0, 255, 0),
    (0, 0, 255),
]
color_index = 0

### RFM95 ###
RFM_RADIO_FREQ_MHZ = 915.0
RFM_CS = digitalio.DigitalInOut(board.RFM_CS)
RFM_RST = digitalio.DigitalInOut(board.RFM_RST)

### RFM95 instance ###
rfm95 = adafruit_rfm9x.RFM9x(board.SPI(), RFM_CS, RFM_RST, RFM_RADIO_FREQ_MHZ)

### PHY params ###
rfm95.high_power = False
rfm95.tx_power = 5
rfm95.signal_bandwidth = 500000
rfm95.spreading_factor = 12
rfm95.coding_rate = 8

### Link layer params ####
rfm95.node = 7
rfm95.destination = 7
rfm95.ack_retries = 5
rfm95.ack_wait = 0.5

### Custom link layer params ###
node_id_list = [1, 2, 3, 4]
node_id = node_id_list[0]

while True:
    pass