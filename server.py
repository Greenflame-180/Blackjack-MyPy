import network
import socket
import time
import gc
import sys
from machine import Timer

# AP Hardware Setup
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
client_registry = {}  # Format: { (ip, port): client_id }
next_available_id = 1

# Configure Socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((IP_ADDRESS, PORT))
server_socket.setblocking(False)

print("--- LIVE DYNAMIC SERVER ONLINE ---")
print(f"IP Address: {IP_ADDRESS} | Port: {PORT}")
print("Type a message and press ENTER to broadcast.\n")

# State management flags
needs_prompt_redraw = True


def server_listener_callback(t):
    global next_available_id, needs_prompt_redraw
    try:
        while True:
            try:
                data, addr = server_socket.recvfrom(1024)
                if not data or len(data) == 0:
                    break

                decoded_text = data.decode('utf-8').strip()

                # Handle connection registration
                if addr not in client_registry:
                    if len(client_registry) < MAX_CLIENTS:
                        client_registry[addr] = next_available_id
                        sys.stdout.write(f"\r\x1b[K[SYSTEM] Client {next_available_id} joined from {addr}\n")
                        next_available_id += 1
                        needs_prompt_redraw = True
                    else:
                        server_socket.sendto(b"[SYSTEM] Server Full.", addr)
                        continue

                sender_id = client_registry[addr]

                if decoded_text == "[Hello System]":
                    continue

                # Wipe current line, print the message, and flag prompt rewrite
                sys.stdout.write(f"\r\x1b[KClient {sender_id}: {decoded_text}\n")
                needs_prompt_redraw = True

                # Route packet out to all other clients
                broadcast_payload = f"Client {sender_id}: {decoded_text}".encode('utf-8')
                for client_addr in client_registry:
                    if client_addr != addr:
                        try:
                            server_socket.sendto(broadcast_payload, client_addr)
                        except OSError:
                            pass
            except OSError:
                break
    except Exception:
        pass


# Initialize background hardware checker
net_timer = Timer(0)
net_timer.init(period=40, mode=Timer.PERIODIC, callback=server_listener_callback)

try:
    while True:
        gc.collect()

        if needs_prompt_redraw:
            sys.stdout.write("\r\x1b[KServer > ")
            needs_prompt_redraw = False

        line = sys.stdin.readline()
        if not line:
            continue

        message = line.strip()
        if message:
            # Display your own message instantly in your terminal log
            sys.stdout.write(f"\r\x1b[KYou (Server): {message}\n")

            outgoing_announcement = f"[SERVER]: {message}".encode('utf-8')
            for client_addr in client_registry:
                try:
                    server_socket.sendto(outgoing_announcement, client_addr)
                except OSError:
                    pass

        needs_prompt_redraw = True

except KeyboardInterrupt:
    print("\nShutting down Server...")
finally:
    net_timer.deinit()
    server_socket.close()
    ap.active(False)
