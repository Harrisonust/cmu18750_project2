# LoRaSPHERE - A LoRa mesh network implementing the RTS/CTS protocol
In this project, we present LoRaSPHERE: a scalable, fully-connected LoRa mesh network. Our project aims to build a distributed mesh network where each node can transmit without a centralized controller. Each node shall be an isotropic transceiver, generating on-board data and attempting to transmit this information to other nodes while minimizing collisions in the network. For this, we plan to use the request-to-send / clear-to-send (RTS/CTS) mechanism as discussed in course lectures (Lecture 9).

## RTS/CTS Description
RTS/CTS is a flow control mechanism typically used in hardware serial communication, but is also in WLANs for virtual carrier sense. Before sending a data packet, a transmitter must "request-to-send" to a receiving node. The receiving node then sends a "clear-to-send" broadcast, reserving the channel for receiving a data message from the transmitter.
In our network, RTS/CTS is implemented on all LoRa nodes as a state machine:

![State Machine-v1 drawio](https://github.com/user-attachments/assets/12cb8509-db25-4fb0-9c28-757dee8f5439)

For our implementation, we use Adafruit Feather RP2040s with an onboard RFM95 LoRa module at 915 MHz. We also include an ALOHA-style network (no collision avoidance mechanism) and a simple lightweight FDMA network, where each receiver only listens on a particular subcarrier.
