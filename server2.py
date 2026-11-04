import network
import socket
import time
import gc  # Import the garbage collector module

SERVER_IP = "192.168.4.1"
PORT = 5005

# 1. Safe Hardware Reset Routine
wlan = network.WLAN(network.STA_IF)
wlan.active(False)
time.sleep(1.0)

wlan.active(True)
time.sleep(1.0)

# 2. Connect using SSID and Password
print("Connecting to Server Wi-Fi...")
wlan.connect('MyESP32S3_AP', 'password123')

# Wait for connection loop
timeout = 30
while not wlan.isconnected() and timeout > 0:
    time.sleep(0.5)
    print(".", end="")
    timeout -= 1

if not wlan.isconnected():
    print("\n[ERROR] Connection timed out.")
else:
    print("\n--- CLIENT CONNECTED SUCCESSFULLY ---")
    print(f"Client IP Address: {wlan.ifconfig()[0]}")

    # 3. Open UDP Socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    print("\n=============================================")
    print("Type your message below and press ENTER to yell it.")
    print("Type 'exit' to stop the script.")
    print("=============================================\n")

    try:
        while True:
            # Force memory cleanup before prompting for text input
            gc.collect()

            # Get data from your keyboard terminal stream
            message = input("Message to send > ")

            if message.strip().lower() == 'exit':
                print("Exiting...")
                break

            # Send the custom string across the wireless channel
            try:
                client_socket.sendto(message.encode('utf-8'), (SERVER_IP, PORT))
                print(f"-> Successfully yelled: '{message}'\n")
            except OSError as e:
                print(f"\n[Socket Error]: {e}. Reopening socket...")
                client_socket.close()
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    except KeyboardInterrupt:
        print("\nStopping Client via Ctrl+C...")
    finally:
        print("Closing socket channel.")
        client_socket.close()
        gc.collect()
