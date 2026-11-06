import network
import socket
import time
import gc
import sys
from machine import Timer

SERVER_IP = "192.168.4.1"
PORT = 5005

# 1. Station Interface Setup
wlan = network.WLAN(network.STA_IF)
wlan.active(False)
time.sleep(0.5)
wlan.active(True)
time.sleep(0.5)

print("Connecting to Wi-Fi Network...")
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

# 2. Configure Non-Blocking Socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_socket.setblocking(False)

# Register node immediately with host server
client_socket.sendto(b"[Hello System]", (SERVER_IP, PORT))

print("Type a message below and press ENTER to transmit.\n")
client_input_buffer = ""


# 3. Hardware Timer Callback for Background Network Listening
def client_listener_callback(t):
    try:
        while True:  # Flush all packets waiting in the stack
            try:
                data, addr = client_socket.recvfrom(1024)
                if data:
                    # Cleanly overwrite line, print network text, restore typing prompt
                    print(f"\r{data.decode('utf-8')}")
                    sys.stdout.write(f"You > {client_input_buffer}")
            except OSError:
                break
    except Exception:
        pass


# Fire off background network scanning independent of console terminal loops
net_timer = Timer(0)
net_timer.init(period=40, mode=Timer.PERIODIC, callback=client_listener_callback)

# 4. Main Console Entry Loop
try:
    sys.stdout.write("You > ")
    while True:
        gc.collect()

        line = sys.stdin.readline()
        if not line:
            continue

        message = line.strip()
        if message:
            if message.lower() == 'exit':
                break

            try:
                client_socket.sendto(message.encode('utf-8'), (SERVER_IP, PORT))
            except OSError:
                print("\n[ERROR] Direct network pipe drop.")

        sys.stdout.write("You > ")

except KeyboardInterrupt:
    print("\nExiting chat environment...")
finally:
    net_timer.deinit()
    client_socket.close()
    wlan.active(False)
    print("Client Offline.")
