import network
import socket
import time

# 1. Start the Hotspot
ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(ssid='MyMicroPythonAP', password='') # Open network, no password

time.sleep(1) # Let the radio turn on
ip_address = ap.ifconfig()[0] # This will be 192.168.4.1

# 2. Open the UDP Socket
PORT = 5005
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((ip_address, PORT))

print(f"--- SERVER STARTED ---")
print(f"Wi-Fi SSID: MyMicroPythonAP")
print(f"Listening on: {ip_address}:{PORT}\n")

try:
    while True:
        # Listen for any incoming UDP message
        data, addr = server_socket.recvfrom(1024)
        print(f"[{addr[0]}]: {data.decode('utf-8')}")

except KeyboardInterrupt:
    print("Stopping Server...")
    server_socket.close()
