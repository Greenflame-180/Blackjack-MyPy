import network
import socket
import time
import gc
import sys
from machine import Timer

SERVER_IP = "192.168.4.1"
PORT = 5005

# Station Setup
wlan = network.WLAN(network.STA_IF)
wlan.active(False)
time.sleep(0.5)
wlan.active(True)
time.sleep(0.5)

print("Connecting to Network...")
wlan.connect('MyESP32S3_AP', 'password123')

timeout = 20
while not wlan.isconnected() and timeout > 0:
    time.sleep(0.5)
    print(".", end="")
    timeout -= 1

if not wlan.isconnected():
    print("\n[CRITICAL] Wi-Fi Connection Failed.")
    sys.exit()

print(f"\nConnected! Local IP: {wlan.ifconfig()[0]}")

# Setup Socket Channels
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_socket.setblocking(False)

# Register with server
client_socket.sendto(b"[Hello System]", (SERVER_IP, PORT))

print("Dynamic Chat Node Initialized. Type and press ENTER.\n")

needs_prompt_redraw = True


def client_listener_callback(t):
    global needs_prompt_redraw
    try:
        while True:
            try:
                data, addr = client_socket.recvfrom(1024)
                if not data:
                    break

                # Clear terminal line, print incoming network packet feed, and trigger prompt refresh
                sys.stdout.write(f"\r\x1b[K{data.decode('utf-8')}\n")
                needs_prompt_redraw = True
            except OSError:
                break
    except Exception:
        pass


# Separate network thread on Timer 1
net_timer = Timer(1)
net_timer.init(period=40, mode=Timer.PERIODIC, callback=client_listener_callback)

try:
    while True:
        gc.collect()

        if needs_prompt_redraw:
            sys.stdout.write("\r\x1b[KYou > ")
            needs_prompt_redraw = False

        line = sys.stdin.readline()
        if not line:
            continue

        message = line.strip()
        if message:
            if message.lower() == 'exit':
                break

            # Render your own sent messages locally on screen instantly
            sys.stdout.write(f"\r\x1b[KYou: {message}\n")

            try:
                client_socket.sendto(message.encode('utf-8'), (SERVER_IP, PORT))
            except OSError:
                sys.stdout.write("\r\x1b[K[ERROR] Packet dropped.\n")

        needs_prompt_redraw = True

except KeyboardInterrupt:
    print("\nDisconnecting...")
finally:
    net_timer.deinit()
    client_socket.close()
    wlan.active(False)
    print("Node Offline.")
