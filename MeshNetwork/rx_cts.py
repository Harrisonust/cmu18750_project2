def recv(rfm95):
    # Look for a new packet
    print(f"[RX {NODE_ID}] Waiting for packets from other nodes")
    packet = rfm95.receive(timeout=1, with_header=True, with_ack=True)

    # If no packet was received during the timeout then None is returned.
    if packet is not None:
        (dest, node, packet_id, flag), payload = packet[:4], packet[4:]
        
        if len(payload) != 250:
            print(f"[RX {NODE_ID}] Payload corrupted {len(payload)=}")
            return

        (color, _) = payload[:3], payload[3:]

        color = tuple(color)        
        if color in color_values:
            color_name = color_values[color]
            print(f"[RX {NODE_ID}] Received packet from src={node} to dst={dest}, color={color}, snr = {rfm95.last_snr}, rssi = {rfm95.last_rssi}")

            # fill led color
            print(f"[RX {NODE_ID}] @@@ Changing color to {color_name} @@@")
            pixel.fill(color)
            num_recv += 1
        else: 
            print(f"[RX {NODE_ID}] color not in the dict {color}")