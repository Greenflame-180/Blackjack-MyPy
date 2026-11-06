import network
import socket
import time
import gc
import uselect
import sys

SERVER_IP = "192.168.4.1"
PORT = 5005

# STA Hardware Setup
wlan = network.WLAN(network.STA_IF)
wlan.active(False)
time.sleep(1.0)
wlan.active(True)
time.sleep(1.0)

print("Connecting to Multi-Client Mesh Network...")
wlan.connect('MyESP32S3_AP', 'password123')

timeout = 30
while not wlan.isconnected() and timeout > 0:
    time.sleep(0.5)
    print(".", end="")
    timeout -= 1

if not wlan.isconnected():
    print("\n[CRITICAL] Network unavailable.")
    sys.exit()

print(f"\n--- CONNECTED --- Local IP: {wlan.ifconfig()[0]}")

# Configure Async Client Socket Channel
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_socket.setblocking(False)

# Initialize Dual-Channel Poller (Listens to network and terminal streams simultaneously)
poller = uselect.poll()
poller.register(client_socket, uselect.POLLIN)
poller.register(sys.stdin, uselect.POLLIN)

print("\n========================================================")
print("CHAT CONTROLS:")
print("-> Simply type text and press ENTER to broadcast globally.")
print("-> Type '@3 your message' to whisper privately to Client 3.")
print("-> Type 'exit' to quit cleanly.")
print("========================================================\n")

# Send initial handshake ping to register with the server and claim an ID number
client_socket.sendto(b"[Hello System]", (SERVER_IP, PORT))

try:
    while True:
        gc.collect()

        # Async event block
        events = poller.poll(150)

        for stream, event in events:
            # Channel A: Incoming Network Transmission Data
            if stream == client_socket and (event & uselect.POLLIN):
                try:
                    data, addr = client_socket.recvfrom(1024)
                    if data:
                        print(f"\n{data.decode('utf-8')}")
                except OSError:
                    pass

            # Channel B: Local Character Entry via Terminal Input Pipeline
            elif stream == sys.stdin and (event & uselect.POLLIN):
                message = sys.stdin.readline().strip()
                if not message:
                    continue

                if message.lower() == 'exit':
                    raise KeyboardInterrupt

                try:
                    client_socket.sendto(message.encode('utf-8'), (SERVER_IP, PORT))
                except OSError:
                    print("Network delivery pipeline dropped a frame.")

except KeyboardInterrupt:
    print("\nDisconnecting Chat node...")
finally:
    client_socket.close()
    wlan.active(False)
    print("Client disconnected.")
