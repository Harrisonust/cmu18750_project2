def send(rfm95):
    # Generate random destination
    rfm95.node = NODE_ID
    rfm95.destination = random.choice(nodes)

    # Generate random payload of colors
    color, color_name = random.choice(list(color_values.items()))

    # Debug statement
    print(f"[TX {NODE_ID}] Sending packet from src={rfm95.node} to dst={rfm95.destination}, color={color}")

    # Send the packet and see if we get an ACK back
    # TODO: use struct
    payload = bytes(color) + b'\x55' * 247
    num_send += 1
    if rfm95.send_with_ack(payload):
        print(f"[TX {NODE_ID}] Received ACK")
        num_ack += 1
        print(f"[TX {NODE_ID}] @@@ Sending color {color_name} @@@")
    else:
        print(f"[TX {NODE_ID}] Failed to receive ACK")