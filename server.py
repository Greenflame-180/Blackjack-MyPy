import network
import time
import socket

# Initialize AP Mode
ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(ssid='MyMicroPythonAP', password='')

print('Access Point is running...', ap.ifconfig())

sio = socket.server()
# KEEP ALIVE LOOP
while True:
    # This keeps the script running indefinitely
    # so the Wi-Fi radio stays active.
    time.sleep(1)
