import network
import socket
import time

SERVER_IP = "192.168.4.1"
PORT = 5005

# 1. Safe Hardware Reset Routine
wlan = network.WLAN(network.STA_IF)
wlan.active(False)
time.sleep(1.0)

wlan.active(True)
time.sleep(1.0)

# 2. Connect using new SSID and Password
print("Connecting to Server Wi-Fi...")
wlan.connect('MyESP32S3_AP', 'password123')

# Wait for connection loop
timeout = 30 # Increased to 15 seconds max
while not wlan.isconnected() and timeout > 0:
    time.sleep(0.5)
    print(".", end="")
    timeout -= 1

if not wlan.isconnected():
    print("\n[ERROR] Connection timed out again.")
    print("Is the server board powered on right next to this one?")
else:
    print("\n--- CLIENT CONNECTED SUCCESSFULLY ---")
    print(f"Client IP Address: {wlan.ifconfig()[0]}")

    # 3. Open UDP Socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # 4. Yell Data
    counter = 1
    try:
        while True:
            message = f"Hello Server! Packet #{counter}"
            client_socket.sendto(message.encode('utf-8'), (SERVER_IP, PORT))
            print(f"Sent: {message}")
            counter += 1
            time.sleep(2)

    except KeyboardInterrupt:
        print("Stopping Client...")
        client_socket.close()
