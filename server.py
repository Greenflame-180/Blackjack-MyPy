import network
import socket
import time

# 1. Force clear any old states
ap = network.WLAN(network.AP_IF)
ap.active(False)
time.sleep(1.0)

ap.active(True)
time.sleep(1.0)

# Configure with an explicit channel (6) and a 11bgn hidden baseline
# ESP32-S3 runs much more stable with a short WPA2 password than completely open
ap.config(
    ssid='MyESP32S3_AP',
    password='password123',
    channel=6,
    authmode=network.AUTH_WPA2_PSK
)

# Wait for interface to settle
time.sleep(1.0)
ip_config = ap.ifconfig()
ip_address = ip_config[0] # Typically 192.168.4.1

print(f"--- SERVER BROADCASTING ---")
print(f"SSID: MyESP32S3_AP | Pass: password123")
print(f"Server IP Address: {ip_address}")

# 2. Open UDP Socket
PORT = 5005
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((ip_address, PORT))

print("Listening for UDP data packets...\n")

try:
    while True:
        data, addr = server_socket.recvfrom(1024)
        print(f"[{addr}]: {data.decode('utf-8')}")

except KeyboardInterrupt:
    print("Stopping Server...")
    server_socket.close()
