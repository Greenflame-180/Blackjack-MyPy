import network
import socket
import time
import gc
import uselect
import sys

# AP Hardware Setup
ap = network.WLAN(network.AP_IF)
ap.active(False)
time.sleep(1.0)
ap.active(True)
time.sleep(1.0)

ap.config(
    ssid='MyESP32S3_AP',
    password='password123',
    channel=6,
    authmode=network.AUTH_WPA2_PSK
)
time.sleep(1.0)

IP_ADDRESS = ap.ifconfig()[0]
PORT = 5005

# Dynamic Client Tracking System (Limit: 10 Clients)
MAX_CLIENTS = 10
client_registry = {}  # Format: { (ip, port): client_id }
next_available_id = 1

# Configure UDP Server Socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((IP_ADDRESS, PORT))
server_socket.setblocking(False)

# Initialize the Listener Engine (Polles both the Radio Socket AND Server Console Input)
poller = uselect.poll()
poller.register(server_socket, uselect.POLLIN)
poller.register(sys.stdin, uselect.POLLIN)

print("--- MULTI-CLIENT ASYNC SERVER ONLINE ---")
print(f"Server IP: {IP_ADDRESS} | Port: {PORT}")
print("Type text in this console to broadcast to ALL clients.")
print("Awaiting network traffic...\n")

try:
    while True:
        gc.collect()

        # Poll for I/O events (100ms block)
        events = poller.poll(100)

        for stream, event in events:
            # Channel A: Data incoming from client nodes over the air
            if stream == server_socket and (event & uselect.POLLIN):
                try:
                    data, addr = server_socket.recvfrom(1024)
                    if not data or len(data) == 0:
                        continue

                    decoded_text = data.decode('utf-8').strip()

                    # Manage Dynamic Client ID Assignment
                    if addr not in client_registry:
                        if len(client_registry) < MAX_CLIENTS:
                            client_registry[addr] = next_available_id
                            print(f"[SYSTEM] Auto-assigned ID {next_available_id} to connection: {addr}")
                            next_available_id += 1
                        else:
                            server_socket.sendto(b"[SYSTEM ERROR] Server full.", addr)
                            continue

                    sender_id = client_registry[addr]

                    # Ignore initial registration handshake ping from printing
                    if decoded_text == "[Hello System]":
                        continue

                    # Handle Private Routing vs Global Broadcast
                    if decoded_text.startswith("@"):
                        try:
                            parts = decoded_text.split(" ", 1)
                            target_id = int(parts[0][1:])  # Extract ID digit accurately
                            payload = parts[1] if len(parts) > 1 else ""

                            target_addr = next((a for a, uid in client_registry.items() if uid == target_id), None)

                            if target_addr:
                                direct_msg = f"[Private from Client {sender_id}]: {payload}"
                                server_socket.sendto(direct_msg.encode('utf-8'), target_addr)
                                print(f"Routed Private: Client {sender_id} -> Client {target_id}")
                            else:
                                server_socket.sendto(f"[SYSTEM] Client {target_id} is offline.".encode('utf-8'), addr)
                        except (ValueError, IndexError):
                            server_socket.sendto(b"[SYSTEM] Invalid whisper format. Use: @[ID] [message]", addr)

                    else:
                        # Broadcast message out to all other clients
                        print(f"Client {sender_id}: {decoded_text}")
                        broadcast_msg = f"Client {sender_id}: {decoded_text}"

                        for client_addr in client_registry:
                            if client_addr != addr:  # Don't echo back to the person who sent it
                                try:
                                    server_socket.sendto(broadcast_msg.encode('utf-8'), client_addr)
                                except OSError:
                                    pass

                except Exception as e:
                    print(f"Radio channel handling error: {e}")

            # Channel B: The Server Admin types a broadcast message into the local terminal
            elif stream == sys.stdin and (event & uselect.POLLIN):
                server_message = sys.stdin.readline().strip()
                if not server_message:
                    continue

                print(f"Server (You): {server_message}")
                outgoing_payload = f"[SERVER ANNOUNCEMENT]: {server_message}".encode('utf-8')

                # Push message down to every registered client
                for client_addr in client_registry:
                    try:
                        server_socket.sendto(outgoing_payload, client_addr)
                    except OSError:
                        pass

except KeyboardInterrupt:
    print("\nShutting down Polling Server...")
finally:
    server_socket.close()
    ap.active(False)
    print("Server cleanly offline.")
