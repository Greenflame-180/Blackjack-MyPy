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

MAX_CLIENTS = 10
client_registry = {}  # Tracks { (ip, port): client_id }
next_available_id = 1

# Configure Async UDP Server Socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((IP_ADDRESS, PORT))
server_socket.setblocking(False)

# Register Radio and Raw Keyboard Streams with Poller Engine
poller = uselect.poll()
poller.register(server_socket, uselect.POLLIN)
poller.register(sys.stdin, uselect.POLLIN)

print("--- INTERACTIVE MULTI-CLIENT SERVER ONLINE ---")
print(f"IP: {IP_ADDRESS} | Port: {PORT}")
print("Start typing down here to broadcast to all nodes.\n")
sys.stdout.write("Server > ")

server_input_buffer = ""

try:
    while True:
        gc.collect()

        # Poll for IO traffic (50ms sleep step)
        events = poller.poll(50)

        for stream, event in events:
            # Channel A: Incoming Network Radio Packets
            if stream == server_socket and (event & uselect.POLLIN):
                try:
                    data, addr = server_socket.recvfrom(1024)
                    if not data or len(data) == 0:
                        continue

                    decoded_text = data.decode('utf-8').strip()

                    # Manage Dynamic ID Mapping System
                    if addr not in client_registry:
                        if len(client_registry) < MAX_CLIENTS:
                            client_registry[addr] = next_available_id
                            # Clear current prompt, log message, restore prompt
                            sys.stdout.write(
                                f"\r[SYSTEM] Client {next_available_id} connected from {addr}\nServer > {server_input_buffer}")
                            next_available_id += 1
                        else:
                            server_socket.sendto(b"[SYSTEM] Server Full.", addr)
                            continue

                    sender_id = client_registry[addr]

                    # Ignore baseline connection handshakes from cluttering feed
                    if decoded_text == "[Hello System]":
                        continue

                    # Print client message locally to server logs safely
                    sys.stdout.write(f"\rClient {sender_id}: {decoded_text}\nServer > {server_input_buffer}")

                    # Broadcast packet out to EVERY other registered client
                    broadcast_payload = f"Client {sender_id}: {decoded_text}".encode('utf-8')
                    for client_addr in client_registry:
                        if client_addr != addr:  # Do not echo to original sender
                            try:
                                server_socket.sendto(broadcast_payload, client_addr)
                            except OSError:
                                pass
                except Exception:
                    pass

            # Channel B: Character-by-Character Server Terminal Input
            elif stream == sys.stdin and (event & uselect.POLLIN):
                char = sys.stdin.read(1)  # Read exactly 1 byte non-blockingly

                if char == '\r' or char == '\n':  # Enter Key pressed
                    if server_input_buffer.strip():
                        # Push message down to all registered clients
                        outgoing_announcement = f"[SERVER]: {server_input_buffer}".encode('utf-8')
                        for client_addr in client_registry:
                            try:
                                server_socket.sendto(outgoing_announcement, client_addr)
                            except OSError:
                                pass

                        sys.stdout.write("\n")
                    else:
                        sys.stdout.write("\n")

                    server_input_buffer = ""
                    sys.stdout.write("Server > ")

                elif char == '\x08' or char == '\x7f':  # Backspace processing
                    if len(server_input_buffer) > 0:
                        server_input_buffer = server_input_buffer[:-1]
                        sys.stdout.write("\b \b")  # Erase character visually from terminal

                else:
                    server_input_buffer += char
                    sys.stdout.write(char)  # Immediate visible visual echo

except KeyboardInterrupt:
    print("\nKilling Server Engine.")
finally:
    server_socket.close()
    ap.active(False)
