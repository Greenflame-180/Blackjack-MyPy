import network
import socket
import time
import gc

# 1. Start the Hotspot cleanly
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
ip_address = ap.ifconfig()[0]

print(f"--- SERVER BROADCASTING ---")
print(f"Server IP Address: {ip_address}")

# 2. Open UDP Socket
PORT = 5005
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((ip_address, PORT))

print("Listening for UDP data packets...\n")

try:
    while True:
        gc.collect()  # Prevent memory leakage

        # Add a micro-delay to keep the CPU from maxing out if it misbehaves
        time.sleep_ms(10)

        try:
            data, addr = server_socket.recvfrom(1024)

            # CRITICAL FIX: Skip empty packets or broken signals
            if not data or len(data) == 0:
                continue

            # Safely decode only valid text data
            text = data.decode('utf-8').strip()
            if text:
                print(f"[{addr[0]}]: {text}")

        except UnicodeError:
            print("Received bad binary packet (failed to decode as text)")
        except OSError as e:
            # If socket drops or hits an error, print it instead of looping garbage
            print(f"Socket tracking glitch: {e}")
            time.sleep(1)

except KeyboardInterrupt:
    print("Stopping Server...")
    server_socket.close()
