import network
import socket
import time
import gc
import sys
from machine import Timer

# 1. Access Point Initialization
ap = network.WLAN(network.AP_IF)
ap.active(False)
time.sleep(0.5)
ap.active(True)
time.sleep(0.5)

ap.config(
    ssid='MyESP32S3_AP',
    password='password123',
    channel=6,
    authmode=network.AUTH_WPA2_PSK
)
time.sleep(0.5)

IP_ADDRESS = ap.ifconfig()[0]
PORT = 5005

MAX_CLIENTS = 10
client_registry = {}  # Tracks { (ip, port): client_id }
next_available_id = 1

# 2. Configure Non-Blocking Socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((IP_ADDRESS, PORT))
server_socket.setblocking(False)

print("--- REAL-TIME UDP SERVER ONLINE ---")
print(f"IP Address: {IP_ADDRESS} | Port: {PORT}")
print("Type here and press ENTER to broadcast to all clients.\n")

server_input_buffer = ""


# 3. Hardware Timer Callback for Background Network Listening
def network_listener_callback(t):
    global next_available_id
    try:
        while True:  # Read all queued packets in the UDP buffer
            try:
                data, addr = server_socket.recvfrom(1024)
                if not data or len(data) == 0:
                    break

                decoded_text = data.decode('utf-8').strip()

                # Manage dynamic client tracking
                if addr not in client_registry:
                    if len(client_registry) < MAX_CLIENTS:
                        client_registry[addr] = next_available_id
                        print(f"\r[SYSTEM] Client {next_available_id} connected from {addr}")
                        sys.stdout.write(f"Server > {server_input_buffer}")
                        next_available_id += 1
                    else:
                        server_socket.sendto(b"[SYSTEM] Server Full.", addr)
                        continue

                sender_id = client_registry[addr]

                # Filter out initial registration pings
                if decoded_text == "[Hello System]":
                    continue

                # Log client message on server terminal
                print(f"\rClient {sender_id}: {decoded_text}")
                sys.stdout.write(f"Server > {server_input_buffer}")

                # Broadcast packet to all other registered clients
                broadcast_payload = f"Client {sender_id}: {decoded_text}".encode('utf-8')
                for client_addr in client_registry:
                    if client_addr != addr:
                        try:
                            server_socket.sendto(broadcast_payload, client_addr)
                        except OSError:
                            pass
            except OSError:
                break  # No data ready to read, exit loop cleanly
    except Exception:
        pass


# Initialize a hardware background timer checking for network frames every 40ms
net_timer = Timer(0)
net_timer.init(period=40, mode=Timer.PERIODIC, callback=network_listener_callback)

# 4. Main Console Entry Loop
try:
    sys.stdout.write("Server > ")
    while True:
        gc.collect()

        # Read full lines safely to prevent serial locking bugs
        line = sys.stdin.readline()
        if not line:
            continue

        server_message = line.strip()
        if server_message:
            # Send server broadcast down to all known clients
            outgoing_announcement = f"[SERVER]: {server_message}".encode('utf-8')
            for client_addr in client_registry:
                try:
                    server_socket.sendto(outgoing_announcement, client_addr)
                except OSError:
                    pass

        sys.stdout.write("Server > ")

except KeyboardInterrupt:
    print("\nShutting down Server Subsystem...")
finally:
    net_timer.deinit()
    server_socket.close()
    ap.active(False)
    print("Server Offline.")
