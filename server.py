import network
import socket
import time
import gc
import uselect

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
server_socket.setblocking(False)  # Set non-blocking for uselect polling

# Initialize the Listener Engine
poller = uselect.poll()
poller.register(server_socket, uselect.POLLIN)

print("--- MULTI-CLIENT ASYNC SERVER ONLINE ---")
print(f"Server IP: {IP_ADDRESS} | Port: {PORT}\n Listening for network traffic...")

try:
    while True:
        gc.collect()

        # Poll for events with a 100ms timeout
        events = poller.poll(100)

        for sock, event in events:
            if event & uselect.POLLIN:
                try:
                    data, addr = server_socket.recvfrom(1024)
                    if not data or len(data) == 0:
                        continue

                    decoded_text = data.decode('utf-8').strip()

                    # 1. Manage Dynamic Client ID Assignment
                    if addr not in client_registry:
                        if len(client_registry) < MAX_CLIENTS:
                            client_registry[addr] = next_available_id
                            print(f"[SYSTEM] Auto-assigned ID {next_available_id} to connection: {addr}")
                            next_available_id += 1
                        else:
                            # Server full rule execution
                            server_socket.sendto(
                                b"[SYSTEM ERROR] Server is at maximum capacity (10 clients). Disconnected.", addr)
                            continue

                    sender_id = client_registry[addr]

                    # 2. Check for targeted communication vs broad broadcast
                    # Syntax: "@3 Hello" routes privately to Client 3. Regular text broadcasts to everyone.
                    if decoded_text.startswith("@"):
                        try:
                            parts = decoded_text.split(" ", 1)
                            target_id = int(parts[0][1:])
                            payload = parts[1] if len(parts) > 1 else ""

                            # Find target address in registry map
                            target_addr = next((a for a, uid in client_registry.items() if uid == target_id), None)

                            if target_addr:
                                direct_msg = f"[Private from Client {sender_id}]: {payload}"
                                server_socket.sendto(direct_msg.encode('utf-8'), target_addr)
                                print(f"Routed: Client {sender_id} -> Client {target_id}")
                            else:
                                server_socket.sendto(f"[SYSTEM] Client {target_id} is not online.".encode('utf-8'),
                                                     addr)
                        except (ValueError, IndexError):
                            server_socket.sendto(b"[SYSTEM] Invalid routing syntax. Use: @[ID] [message]", addr)

                    else:
                        # Standard Broadcast routing loop to all other active listeners
                        print(f"Client {sender_id}: {decoded_text}")
                        broadcast_msg = f"Client {sender_id}: {decoded_text}"

                        for client_addr in client_registry:
                            if client_addr != addr:  # Avoid mirroring back to sender
                                try:
                                    server_socket.sendto(broadcast_msg.encode('utf-8'), client_addr)
                                except OSError:
                                    pass

                except Exception as e:
                    print(f"Event handler warning: {e}")

except KeyboardInterrupt:
    print("\nShutting down Polling Server...")
finally:
    server_socket.close()
    ap.active(False)
    print("Server cleanly offline.")
