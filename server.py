import network
import socket
import time
import gc

# 1. Clean Hardware Initialization for Access Point
ap = network.WLAN(network.AP_IF)
ap.active(False)
time.sleep(1.0)  # Allow hardware registers to clear completely

ap.active(True)
time.sleep(1.0)  # Allow driver layer to settle

ap.config(
    ssid='MyESP32S3_AP',
    password='password123',
    channel=6,
    authmode=network.AUTH_WPA2_PSK
)
time.sleep(1.0)

# Extract the Access Point's internal IP config
ip_config = ap.ifconfig()
ip_address = ip_config[0]

print("--- SERVER SUBSYSTEM INITIALIZED ---")
print(f"SSID: MyESP32S3_AP | Password: password123")
print(f"Server IP Address: {ip_address}\n")

# 2. Open UDP Socket Channel
PORT = 5005
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((ip_address, PORT))

print(f"UDP Radio Server listening on port {PORT}...")
print("Awaiting incoming text broadcasts...\n")

try:
    while True:
        gc.collect()  # Maintain continuous RAM cleanup
        time.sleep_ms(10)  # CPU pace brake to suppress phantom feedback loops

        try:
            data, addr = server_socket.recvfrom(1024)

            # Filter out empty or broken frame buffers immediately
            if not data or len(data) == 0:
                continue

            # Attempt safe string conversion
            decoded_text = data.decode('utf-8').strip()
            if decoded_text:
                print(f"Received from {addr[0]}:{addr[1]} -> {decoded_text}")

        except UnicodeError:
            print("Dropped packet: Unable to decode payload into valid UTF-8 text.")
        except OSError as e:
            print(f"Socket operation warning: {e}")
            time.sleep(1)

except KeyboardInterrupt:
    print("\nShutting down Server environment...")
finally:
    server_socket.close()
    ap.active(False)
    print("Server cleanly offline.")
