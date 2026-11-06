import network
import socket
import time
import gc
import sys
from machine import Timer

class ClientEventListener:
    def __init__(self, server_ip, port):
        self.server_ip = server_ip
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setblocking(False)
        self.timer = Timer(1)
        self.on_message_callback = None

    def on_message(self, callback):
        self.on_message_callback = callback

    def start(self):
        # Fire Handshake registration string
        self.socket.sendto(b"[Hello System]", (self.server_ip, self.port))
        self.timer.init(period=40, mode=Timer.PERIODIC, callback=self._check_network)

    def emit(self, text):
        try:
            self.socket.sendto(text.encode('utf-8'), (self.server_ip, self.port))
        except OSError:
            pass

    def _check_network(self, t):
        try:
            while True:
                try:
                    data, addr = self.socket.recvfrom(1024)
                    if not data:
                        break
                    if self.on_message_callback:
                        self.on_message_callback(data.decode('utf-8'))
                except OSError:
                    break
        except Exception:
            pass

# --- MAIN APP ARCHITECTURE (NO LOOPS) ---

wlan = network.WLAN(network.STA_IF)
wlan.active(False); time.sleep(0.5); wlan.active(True); time.sleep(0.5)
print("Connecting...")
wlan.connect('MyESP32S3_AP', 'password123')

timeout = 20
while not wlan.isconnected() and timeout > 0:
    time.sleep(0.5); timeout -= 1

if not wlan.isconnected():
    sys.exit()

print(f"Connected to dynamic network. Local IP: {wlan.ifconfig()[0]}")

client = ClientEventListener("192.168.4.1", 5005)

# Defining your clean Socket-style event listener
@client.on_message
def on_broadcast_received(data):
    sys.stdout.write(f"\r\x1b[K{data}\nYou > ")

# Start listening
client.start()

try:
    while True:
        gc.collect()
        sys.stdout.write("\r\x1b[KYou > ")
        line = sys.stdin.readline()
        if line:
            msg = line.strip()
            if msg:
                if msg.lower() == 'exit':
                    break
                sys.stdout.write(f"\r\x1b[KYou: {msg}\n")
                client.emit(msg)  # Emit text packet directly upward
except KeyboardInterrupt:
    pass
finally:
    client.timer.deinit()
    client.socket.close()
    wlan.active(False)
    print("\nOffline.")
