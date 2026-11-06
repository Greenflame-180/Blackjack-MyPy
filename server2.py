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

print("Connecting to Server...")
wlan.connect('MyESP32S3_AP', 'password123')

timeout = 30
while not wlan.isconnected() and timeout > 0:
    time.sleep(0.5)
    print(".", end="")
    timeout -= 1

if not wlan.isconnected():
    print("\n[CRITICAL] AP Handshake Failed.")
    sys.exit()

print(f"\nConnected! Local Node IP: {wlan.ifconfig()[0]}")

# Setup Async Client Socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_socket.setblocking(False)

# Register Network Stream and Standard Keyboard Streams with Poller Engine
poller = uselect.poll()
poller.register(client_socket, uselect.POLLIN)
poller.register(sys.stdin, uselect.POLLIN)

# Send initial baseline ping to secure ID registry slot on server
client_socket.sendto(b"[Hello System]", (SERVER_IP, PORT))

print("Start typing to chat in real-time.\n")
sys.stdout.write("You > ")

client_input_buffer = ""

try:
    while True:
        gc.collect()

        events = poller.poll(50)

        for stream, event in events:
            # Channel A: Incoming text packet streams from Server/Other Clients
            if stream == client_socket and (event & uselect.POLLIN):
                try:
                    data, addr = client_socket.recvfrom(1024)
                    if data:
                        # Clear line visually, display incoming message, rewrite active buffer text
                        sys.stdout.write(f"\r{data.decode('utf-8')}\nYou > {client_input_buffer}")
                except OSError:
                    pass

            # Channel B: Character-by-Character Terminal Keyboard Input
            elif stream == sys.stdin and (event & uselect.POLLIN):
                char = sys.stdin.read(1)  # Harvest single key input byte

                if char == '\r' or char == '\n':  # Enter Key pressed
                    cleaned_sendable = client_input_buffer.strip()

                    if cleaned_sendable.lower() == 'exit':
                        raise KeyboardInterrupt

                    if cleaned_sendable:
                        try:
                            client_socket.sendto(cleaned_sendable.encode('utf-8'), (SERVER_IP, PORT))
                        except OSError:
                            sys.stdout.write("\n[Packet drop warning]\n")

                    sys.stdout.write("\n")
                    client_input_buffer = ""
                    sys.stdout.write("You > ")

                elif char == '\x08' or char == '\x7f':  # Backspace handling
                    if len(client_input_buffer) > 0:
                        client_input_buffer = client_input_buffer[:-1]
                        sys.stdout.write("\b \b")  # Pop character out of screen buffer view

                else:
                    client_input_buffer += char
                    sys.stdout.write(char)  # Immediate visible visual echo

except KeyboardInterrupt:
    print("\nExiting chat loop...")
finally:
    client_socket.close()
    wlan.active(False)
    print("Node Offline.")
