import network
import socket
import time
import gc

SERVER_IP = "192.168.4.1"
PORT = 5005

# 1. Clean Hardware Initialization for Station Mode
wlan = network.WLAN(network.STA_IF)
wlan.active(False)
time.sleep(1.0)  # Allow hardware registers to clear completely

wlan.active(True)
time.sleep(1.0)  # Allow driver layer to settle

# 2. Connect to the Server Hotspot
print("Connecting to Server Wi-Fi...")
wlan.connect('MyESP32S3_AP', 'password123')

# Connection stability validation loop (30 counts max)
timeout = 30
while not wlan.isconnected() and timeout > 0:
    time.sleep(0.5)
    print(".", end="")
    timeout -= 1

if not wlan.isconnected():
    print("\n[CRITICAL ERROR] Connection to server hotspot timed out.")
    print("Ensure the server board is powered up and sitting nearby.")
else:
    client_ip = wlan.ifconfig()[0]
    print("\n--- CLIENT CONNECTED SUCCESSFULLY ---")
    print(f"Local Client IP: {client_ip}")

    # 3. Open UDP Socket Channel
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    print("\n========================================================")
    print("Instructions: Type your phrase below and press ENTER.")
    print("Type 'exit' to terminate the script process safely.")
    print("========================================================\n")

    try:
        while True:
            gc.collect()  # Flush old string buffer history out of RAM before fresh input

            # Fetch terminal character input array
            message = input("Text to send > ")

            # Process clean string checking
            cleaned_message = message.strip()
            if not cleaned_message:
                continue

            if cleaned_message.lower() == 'exit':
                print("Exiting runtime client loop...")
                break

            # Attempt to push data buffer to the targeted endpoint
            try:
                client_socket.sendto(cleaned_message.encode('utf-8'), (SERVER_IP, PORT))
                print(f"-> Package sent successfully.\n")
            except OSError as socket_err:
                print(f"Transmission leak detected ({socket_err}). Recycling socket pipeline...")
                client_socket.close()
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    except KeyboardInterrupt:
        print("\nHalting Client via user interruption command...")
    finally:
        print("De-allocating socket channels.")
        client_socket.close()
        wlan.active(False)
        gc.collect()
        print("Client completely offline.")
